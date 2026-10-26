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
from functools import partial
from threading import Lock

import elasticapm
from brewtils.models import BaseModel, Event, Garden, Operation
from elasticapm import Client
from elasticapm.metrics.base_metrics import MetricSet
from prometheus_client.core import REGISTRY, GaugeMetricFamily
from prometheus_client.registry import Collector

import beer_garden.config as config
import beer_garden.db.api as db
import beer_garden.events
from beer_garden.garden import calculate_garden_statistics

logger = logging.getLogger(__name__)


class CumulativeCollector(Collector):
    def __init__(
        self, collector, name, description=None, labels=None, metric_keys=None
    ):
        self._lock = Lock()
        self._name = name
        self._description = description
        self._labels = [] if labels is None else labels
        self._collector = collector
        self._metric_keys = metric_keys

    def collect(self):
        with self._lock:
            # 1. Execute Query
            values = self._collector()

        # 2. Create your metrics using the calculated delta window
        gauge = GaugeMetricFamily(
            self._name,
            self._description,
            labels=(
                self._labels
                if self._metric_keys is None
                else (self._labels + ["METRIC"])
            ),
        )

        # 4. Apply Values
        for value in values:

            if self._metric_keys is None:
                labels = []
                for label_key in self._labels:
                    labels.append(value.get(label_key, ""))
                gauge.add_metric(labels, value.get("count", 0))
            else:
                for metric_key in self._metric_keys:
                    if metric_key in value:
                        labels = []
                        for label_key in self._labels:
                            labels.append(value.get(label_key, ""))
                        labels.append(metric_key)
                        gauge.add_metric(labels, value.get(metric_key, 0))

        yield gauge


def garden_os_metrics():
    # Collect the OS CPU/MEM metrics provided by Garden Metadata

    local_garden = config.get("garden.name")
    gardens = db.query(
        Garden,
        include_fields=["metadata", "name"],
        filter_params={"name__ne": local_garden},
    )

    total = []

    total.append(calculate_garden_statistics() | {"GARDEN_NAME": local_garden})

    keys = [
        "CPU_USAGE",
        "CPU_BG_USAGE",
        "MEM_TOTAL",
        "MEM_USAGE",
        "MEM_BG_USAGE",
        "MEM_AVAILABLE",
        "MEM_FREE",
    ]

    for garden in gardens:
        mapped_keys = {}

        for key in keys:
            if key in garden.metadata:
                mapped_keys[key] = garden.metadata[key]

        if len(mapped_keys) > 0:
            mapped_keys["GARDEN_NAME"] = garden.name
            total.append(mapped_keys)

    return total


def setup_metrics():
    REGISTRY.register(
        CumulativeCollector(
            partial(garden_os_metrics),
            name="bg_garden_os_metrics",
            description="Garden OS Metrics CPU/MEM",
            labels=["GARDEN_NAME"],
            metric_keys=[
                "CPU_USAGE",
                "CPU_BG_USAGE",
                "MEM_TOTAL",
                "MEM_USAGE",
                "MEM_BG_USAGE",
                "MEM_AVAILABLE",
                "MEM_FREE",
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
