# -*- coding: utf-8 -*-
"""Metrics Service

The metrics service manages:
* Connectivity to the Prometheus Server
* Creating default summary views in Prometheus
* Publishing `Request` metrics
"""
import datetime
import json
import logging
import re
import sys
import time
from functools import partial
from threading import Lock

import elasticapm
from brewtils.models import BaseModel, Event, Operation, Request
from elasticapm import Client
from elasticapm.metrics.base_metrics import MetricSet
from prometheus_client.core import REGISTRY, GaugeMetricFamily, SummaryMetricFamily
from prometheus_client.registry import Collector

import beer_garden.config as config
import beer_garden.db.api as db
import beer_garden.events
from beer_garden.garden import get_gardens

logger = logging.getLogger(__name__)


class SummaryCollector(Collector):
    def __init__(self, collector, name, description=None, labels=None):
        self._lock = Lock()
        self._name = name
        self._description = description
        self._labels = [] if labels is None else labels
        self._collector = collector

    def collect(self):
        with self._lock:
            # 1. Execute Query
            values = self._collector()

        summary = SummaryMetricFamily(
            self._name,
            self._description,
            labels=self._labels,
        )

        # 4. Apply Values
        for value in values:
            labels = []
            for label_key in self._labels:
                labels.append(value[label_key])

            summary.add_metric(labels, value["count"], value["sum_value"])
        yield summary


class CumulativeCollector(Collector):
    def __init__(self, collector, name, description=None, labels=None):
        self._lock = Lock()
        self._name = name
        self._description = description
        self._labels = [] if labels is None else labels
        self._collector = collector

    def collect(self):
        with self._lock:
            # 1. Execute Query
            values = self._collector()

        # 2. Create your metrics using the calculated delta window
        gauge = GaugeMetricFamily(
            self._name,
            self._description,
            labels=self._labels,
        )

        # 4. Apply Values
        for value in values:
            labels = []
            for label_key in self._labels:
                labels.append(value[label_key])

            gauge.add_metric(labels, value["count"])
        yield gauge


class TimeWindowCollector(Collector):
    def __init__(self, collector, name, description=None, labels=None):
        # Initialize the last scrape timestamp (Could be last 15 minutes if we wanted)
        self._last_scrape_time = time.time()
        self._lock = Lock()
        self._name = name
        self._description = description
        self._labels = [] if labels is None else labels
        self._collector = collector

    def collect(self):
        # 1. Capture the exact current time of the incoming query
        current_scrape_time = time.time()

        with self._lock:
            # 2. Calculate the elapsed time window (in seconds)
            time_window = current_scrape_time - self._last_scrape_time

            # 3. Execute Query
            values = self._collector(time_window)
            # Update state for the next scrape iteration
            self._last_scrape_time = current_scrape_time

        # 4. Create your metrics using the calculated delta window
        gauge = GaugeMetricFamily(
            self._name,
            self._description,
            labels=self._labels,
        )

        # 5. Apply Values
        for value in values:
            labels = []
            for label_key in self._labels:
                labels.append(value[label_key])

            gauge.add_metric(labels, value["count"])
        yield gauge


def request_garden_totals():
    pipeline = [
        {
            "$group": {
                "_id": {
                    "namespace": "$namespace",
                    "system": "$system",
                    "system_version": "$system_version",
                    "instance_name": "$instance_name",
                    "command": "$command",
                    "target_garden": "$target_garden",
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "namespace": "$_id.namespace",
                "system": "$_id.system",
                "system_version": "$_id.system_version",
                "instance_name": "$_id.instance_name",
                "command": "$_id.command",
                "target_garden": "$_id.target_garden",
                "count": "$count",
            }
        },
    ]

    result = db.aggregation(Request, pipeline=pipeline)

    return result


def request_garden_completed_totals():
    pipeline = [
        {
            "$match": {
                "status": {"$in": ["CANCELED", "SUCCESS", "ERROR", "INVALID"]},
            }
        },
        {
            "$group": {
                "_id": {
                    "namespace": "$namespace",
                    "system": "$system",
                    "system_version": "$system_version",
                    "instance_name": "$instance_name",
                    "command": "$command",
                    "status": "$status",
                    "target_garden": "$target_garden",
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "namespace": "$_id.namespace",
                "system": "$_id.system",
                "system_version": "$_id.system_version",
                "instance_name": "$_id.instance_name",
                "command": "$_id.command",
                "status": "$_id.status",
                "target_garden": "$_id.target_garden",
                "count": "$count",
            }
        },
    ]

    result = db.aggregation(Request, pipeline=pipeline)

    return result


def request_garden_status_metrics(statusList: list[str], time_window: int = 900):
    # Must provide at least one status
    if len(statusList) < 1:
        return []

    pipeline = [
        {
            "$match": {
                "status": {"$in": statusList},
                "updated_at": {
                    "$gte": datetime.datetime.now(datetime.timezone.utc)
                    - datetime.timedelta(seconds=time_window)
                },
            }
        },
        {
            "$group": {
                "_id": {
                    "namespace": "$namespace",
                    "system": "$system",
                    "system_version": "$system_version",
                    "instance_name": "$instance_name",
                    "target_garden": "$target_garden",
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "namespace": "$_id.namespace",
                "system": "$_id.system",
                "system_version": "$_id.system_version",
                "instance_name": "$_id.instance_name",
                "target_garden": "$_id.target_garden",
                "count": "$count",
            }
        },
    ]

    # Expect list and empty list ok
    result = db.aggregation(Request, pipeline=pipeline)

    return result


def request_garden_plugin_command_latency_metrics(interval: int = 15):
    # Calculates the avg latency for a plugin

    pipeline = [
        # Stage 1: Filter by completed status
        {
            "$match": {
                "status": {"$in": ["CANCELED", "SUCCESS", "ERROR", "INVALID"]},
            }
        },
        # Stage 2: Calculate the delta for CREATED to COMPLETED
        {
            "$addFields": {
                "delta": {
                    "$dateDiff": {
                        "startDate": "$created_at",
                        "endDate": "$status_updated_at",
                        "unit": "second",
                    }
                }
            }
        },
        # Stage 3: Calculate the average of all deltas
        {
            "$group": {
                "_id": {
                    "namespace": "$namespace",
                    "system": "$system",
                    "system_version": "$system_version",
                    "instance_name": "$instance_name",
                    "command": "$command",
                    "status": "$status",
                    "target_garden": "$target_garden",
                },
                "count": {"$sum": 1},
                "sum_value": {"$sum": "$delta"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "namespace": "$_id.namespace",
                "system": "$_id.system",
                "system_version": "$_id.system_version",
                "instance_name": "$_id.instance_name",
                "command": "$_id.command",
                "status": "$_id.status",
                "target_garden": "$_id.target_garden",
                "count": "$count",
                "sum_value": "$sum_value",
            }
        },
    ]
    result = db.aggregation(Request, pipeline=pipeline)

    if result is not None:
        return result

    # Can't find a result
    return []


def request_garden_send_latency_metrics(interval: int = 15):
    # Calculated the average trip down to a Target Garden from this Garden in seconds

    local_garden = config.get("garden.name")
    gardens = get_gardens(include_local=False)

    total = []
    for garden in gardens:
        pipeline = [
            # Stage 1: Filter by source_garden, target_garden, status, updated_at,
            # and metadata fields
            {
                "$match": {
                    "source_garden": local_garden,
                    "target_garden": garden.name,
                    "status": "SUCCESS",
                    "updated_at": {
                        "$gte": datetime.datetime.now(datetime.timezone.utc)
                        - datetime.timedelta(minutes=interval)
                    },
                    f"metadata.CREATED_{local_garden}": {"$exists": True, "$ne": None},
                    f"metadata.CREATED_{garden.name}": {"$exists": True, "$ne": None},
                    "$expr": {
                        "$gt": [
                            f"$metadata.CREATED_{garden.name}",
                            f"$metadata.CREATED_{local_garden}",
                        ]
                    },
                }
            },
            # Stage 2: Calculate the delta for CREATED to traverse from Local to Target garden
            {
                "$addFields": {
                    "delta": {
                        "$subtract": [
                            f"$metadata.CREATED_{garden.name}",
                            f"$metadata.CREATED_{local_garden}",
                        ]
                    }
                }
            },
            # Stage 3: Calculate the average of all deltas
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "sum_value": {"$avg": {"$divide": ["$delta", 1000]}},
                }
            },
        ]
        result = db.aggregation(Request, pipeline=pipeline)

        if result is not None and len(result) > 0:
            total.append(
                {
                    "target_garden": garden.name,
                    "count": result[0]["count"],
                    "sum_value": result[0]["sum_value"],
                }
            )

    return total


def request_garden_return_latency_metrics(target_garden: str, interval: int = 15):
    # Calcualted the average trip from a Target Garden to this Garden is seconds

    local_garden = config.get("garden.name")
    gardens = get_gardens(include_local=False)

    total = []
    for garden in gardens:
        pipeline = [
            # Stage 1: Filter by target_garden, status, updated_at, and metadata fields
            {
                "$match": {
                    "target_garden": garden.name,
                    "status": "SUCCESS",
                    "updated_at": {
                        "$gte": datetime.datetime.now(datetime.timezone.utc)
                        - datetime.timedelta(minutes=interval)
                    },
                    f"metadata.SUCCESS_{local_garden}": {"$exists": True, "$ne": None},
                    f"metadata.SUCCESS_{garden.name}": {"$exists": True, "$ne": None},
                    "$expr": {
                        "$gt": [
                            f"$metadata.SUCCESS_{local_garden}",
                            f"$metadata.SUCCESS_{garden.name}",
                        ]
                    },
                }
            },
            # Stage 2: Calculate the delta for SUCCESS to traverse from Target to Local garden
            {
                "$addFields": {
                    "delta": {
                        "$subtract": [
                            f"$metadata.SUCCESS_{local_garden}",
                            f"$metadata.SUCCESS_{garden.name}",
                        ]
                    }
                }
            },
            # Stage 3: Calculate the average of all deltas
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "sum_value": {"$avg": {"$divide": ["$delta", 1000]}},
                }
            },
        ]
        result = db.aggregation(Request, pipeline=pipeline)

        if result is not None and len(result) > 0:
            total.append(
                {
                    "target_garden": garden.name,
                    "count": result[0]["count"],
                    "sum_value": result[0]["sum_value"],
                }
            )

    return total


def setup_metrics():
    REGISTRY.register(
        TimeWindowCollector(
            partial(request_garden_status_metrics, ["CREATED"]),
            name="bg_queued_requests",
            description="Number of CREATED requests",
            labels=[
                "namespace",
                "system",
                "system_version",
                "instance_name",
                "target_garden",
            ],
        )
    )
    REGISTRY.register(
        TimeWindowCollector(
            partial(request_garden_status_metrics, ["IN_PROGRESS"]),
            name="bg_in_progress_requests",
            description="Number of IN_PROGRESS requests",
            labels=[
                "namespace",
                "system",
                "system_version",
                "instance_name",
                "target_garden",
            ],
        )
    )
    REGISTRY.register(
        TimeWindowCollector(
            partial(request_garden_status_metrics, ["SUCCESS"]),
            name="bg_success_requests",
            description="Number of SUCCESS requests",
            labels=[
                "namespace",
                "system",
                "system_version",
                "instance_name",
                "target_garden",
            ],
        )
    )
    REGISTRY.register(
        TimeWindowCollector(
            partial(request_garden_status_metrics, ["ERROR"]),
            name="bg_error_requests",
            description="Number of ERROR requests",
            labels=[
                "namespace",
                "system",
                "system_version",
                "instance_name",
                "target_garden",
            ],
        )
    )
    REGISTRY.register(
        TimeWindowCollector(
            partial(
                request_garden_status_metrics,
                ["CANCELED", "SUCCESS", "ERROR", "INVALID"],
            ),
            name="bg_completed_requests",
            description="Number of completed requests",
            labels=[
                "namespace",
                "system",
                "system_version",
                "instance_name",
                "target_garden",
            ],
        )
    )
    REGISTRY.register(
        TimeWindowCollector(
            partial(
                request_garden_status_metrics,
                [
                    "CREATED",
                    "RECEIVED",
                    "IN_PROGRESS",
                    "CANCELED",
                    "SUCCESS",
                    "ERROR",
                    "INVALID",
                ],
            ),
            name="bg_requests",
            description="Number of requests",
            labels=[
                "namespace",
                "system",
                "system_version",
                "instance_name",
                "target_garden",
            ],
        )
    )
    REGISTRY.register(
        CumulativeCollector(
            partial(request_garden_totals),
            name="bg_requests_total",
            description="Total number of requests",
            labels=[
                "namespace",
                "system",
                "system_version",
                "instance_name",
                "command",
                "target_garden",
            ],
        )
    )
    REGISTRY.register(
        CumulativeCollector(
            partial(request_garden_completed_totals),
            name="bg_completed_requests_total",
            description="Total number of completed requests",
            labels=[
                "namespace",
                "system",
                "system_version",
                "instance_name",
                "command",
                "status",
                "target_garden",
            ],
        )
    )
    REGISTRY.register(
        SummaryCollector(
            partial(request_garden_send_latency_metrics),
            name="bg_garden_send_latency",
            description="Total number of seconds garden is taking to send",
            labels=["target_garden"],
        )
    )
    REGISTRY.register(
        SummaryCollector(
            partial(request_garden_return_latency_metrics, "downstream"),
            name="bg_garden_return_latency",
            description="Total number of seconds each garden is taking to receive",
            labels=["target_garden"],
        )
    )
    REGISTRY.register(
        SummaryCollector(
            partial(request_garden_plugin_command_latency_metrics),
            name="bg_plugin_command_latency_seconds",
            description="Plugin command latency in seconds",
            labels=[
                "namespace",
                "system",
                "instance_name",
                "system_version",
                "command",
                "status",
                "target_garden",
            ],
        )
    )


def request_latency(start_time):
    """Measure request latency in seconds as a float."""
    return (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()


def initialize_elastic_client(label: str):
    """Initializes the Elastic APM client connection

    Args:
        label (str): Name of services being tracked
    """
    if config.get("metrics.elastic.enabled"):
        client = Client(
            {
                "SERVICE_NAME": (
                    f"{re.sub(r'[^a-zA-Z0-9 _-]', '', config.get('garden.name'))}"
                    f"-{label}"
                ),
                "SERVER_URL": config.get("metrics.elastic.url"),
            }
        )

        client.metrics.register(ProcessorMetricsSet)


def _calculate_size(field) -> int:
    """Determine if the field is a large dataset that should be stored in GridFS"""

    total_size = sys.getsizeof(field)

    if isinstance(field, dict):
        total_size += sys.getsizeof(json.dumps(field))

    elif isinstance(field, list):
        for item in field:
            total_size += _calculate_size(item)
    elif isinstance(field, BaseModel):
        for attribute in dir(field):
            if not callable(attribute) and not attribute.startswith("_"):
                total_size += _calculate_size(getattr(field, attribute))

    return total_size


def extract_custom_context(result) -> None:
    """Extracts values from models to be tracked in the custom context fields

    Args:
        result: Any object to be tracked
    """

    if elasticapm.get_trace_parent_header():

        if hasattr(result, "metadata") and result.metadata:
            elasticapm.label(**result.metadata)

        if isinstance(result, Operation):
            return extract_custom_context(result.model)
        if isinstance(result, Event):
            elasticapm.label(event_name=result.name)
            elasticapm.label(event_garden=result.garden)

            if hasattr(result, "payload"):
                return extract_custom_context(result.payload)

        if hasattr(result, "id") and result.id:
            elasticapm.label(mongo_id=result.id)

        elasticapm.label(result_type=str(type(result)))


class CollectMetrics(elasticapm.capture_span):
    def __init__(self, span_type=None, name=None, trace_parent_header=None):
        if not config.get("metrics.elastic.enabled"):
            return

        if elasticapm.get_trace_parent_header() is not None:
            super().__init__(
                name=name,
                span_type=span_type,
                links=[
                    elasticapm.trace_parent_from_string(
                        elasticapm.get_trace_parent_header()
                    )
                ],
            )
            self.use_capture_span = True
            return

        self.use_capture_span = False
        self.name = name
        self.type = span_type
        self.client = None
        self.trace_parent_header = trace_parent_header

    def __enter__(self):

        if not config.get("metrics.elastic.enabled"):
            return self

        if self.use_capture_span:
            return super().__enter__()

        self.client = get_apm_client(
            self.type, self.name, trace_id=self.trace_parent_header
        )

        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):

        if not config.get("metrics.elastic.enabled"):
            return

        if self.use_capture_span:
            return super().__exit__(
                exception_type, exception_value, exception_traceback
            )

        # ADD LABELS
        if exception_type:
            self.client.capture_exception(
                exec_info=(exception_type, exception_value, exception_traceback)
            )
            self.client.end_transaction(result="failure")
        if self.client:
            self.client.end_transaction(result="success")


def get_apm_client(
    transaction_type, transaction_name, trace_parent=None, trace_id=None
):
    """Get the Elastic APM client

    Args:
        transaction_type: Type of transaction that is being recorded
        transaction_name: Name of the transaction

    Returns:
        Client: Elastic APM client
    """
    if config.get("metrics.elastic.enabled"):
        client = elasticapm.get_client()
        if client:

            if not trace_parent:
                if not trace_id:
                    trace_id = elasticapm.get_trace_parent_header()
                if trace_id:
                    trace_parent = elasticapm.trace_parent_from_string(trace_id)

            client.begin_transaction(
                transaction_type=transaction_type,
                trace_parent=trace_parent,
            )
            elasticapm.set_transaction_name(transaction_name)
            return client
    return None


class ProcessorMetricsSet(MetricSet):
    def __init__(self, registry) -> None:
        self.logger = logging.getLogger(__name__)
        super(ProcessorMetricsSet, self).__init__(registry)

    def before_collect(self):
        if hasattr(beer_garden.events.manager, "_processors"):
            for processor in beer_garden.events.manager._processors:
                if hasattr(processor, "queue_depth"):
                    depth = processor.queue_depth()
                    if depth > 0:
                        self.logger.debug(
                            "processor_metrics."
                            f"{processor._handler_tag.replace(' ', '_').lower()}"
                            f" == {depth}"
                        )
                    self.gauge(
                        f"processor_metrics.{processor._handler_tag.replace(' ', '_').lower()}",
                    ).val = depth
            if hasattr(beer_garden.events.manager, "queue_depth"):
                depth = beer_garden.events.manager.queue_depth()
                if depth > 0:
                    self.logger.debug(f"processor_metrics.events_manager == {depth}")
                self.gauge("processor_metrics.events_manager").val = depth
