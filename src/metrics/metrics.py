# -*- coding: utf-8 -*-
"""Metrics Service

The metrics service manages:
* Connectivity to the Prometheus Server
* Creating default summary views in Prometheus
* Publishing `Request` metrics
"""
import argparse
import datetime
import logging
import sys
import time
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Lock

from brewtils.models import Garden, Request
from brewtils.stoppable_thread import StoppableThread
from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY, GaugeMetricFamily, SummaryMetricFamily
from prometheus_client.exposition import MetricsHandler
from prometheus_client.registry import Collector
from pymongo.errors import ServerSelectionTimeoutError
from yapconf import YapconfSpec

import beer_garden.db.api as db
import beer_garden.db.mongo as db_mongo
from beer_garden.config import _DB_SPEC, _GARDEN_SPEC
from beer_garden.db.mongo.api import create_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add yapconf spec
my_spec = YapconfSpec({"db": _DB_SPEC, "garden": _GARDEN_SPEC}, env_prefix="BG_")

# Support CLI args via argparse
parser = argparse.ArgumentParser()
my_spec.add_arguments(parser)
cli_args = vars(parser.parse_args(sys.argv[1:]))

# Add sources
my_spec.add_source("cli_args", "dict", data=cli_args)
my_spec.add_source("ENVIRONMENT", "environment")
config = my_spec.load_config(cli_args, "ENVIRONMENT")

# Make connection to mongo
create_connection(db_config=config.get("db"))

_model_map = {}
for model_name in db_mongo.models.__all__:
    mongo_class = getattr(db_mongo.models, model_name)

    brewtils_model = getattr(mongo_class, "brewtils_model", None)

    if brewtils_model:
        _model_map[brewtils_model] = mongo_class


def aggregation(model_class: any, pipeline: list = None) -> list:

    query_set = _model_map[model_class].objects
    cursor = query_set.aggregate(pipeline)

    results = []

    for document in cursor:
        results.append(document)
    return results


db.aggregation = aggregation


class PrometheusServer(StoppableThread):
    """Wraps a ThreadingHTTPServer to serve Prometheus metrics"""

    def __init__(self, host, port):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Prometheus Server"

        self._host = host
        self._port = port

        # Basically prometheus_client.exposition.start_http_server
        metrics_handler = MetricsHandler.factory(REGISTRY)
        self.httpd = ThreadingHTTPServer((host, port), metrics_handler)

        super(PrometheusServer, self).__init__(
            logger=self.logger, name="PrometheusServer"
        )

    def run(self):

        self.logger.info(f"Starting {self.display_name} on {self._host}:{self._port}")
        self.httpd.serve_forever()

        self.logger.info(f"{self.display_name} is stopped")

    def stop(self):
        self.httpd.shutdown()


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
                labels.append(value.get(label_key, ""))

            summary.add_metric(labels, value.get("count", 0), value.get("sum_value", 0))
        yield summary


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
                labels.append(value.get(label_key, ""))

            gauge.add_metric(labels, value.get("count", 0))
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

    try:
        result = db.aggregation(Request, pipeline=pipeline)
    except ServerSelectionTimeoutError:
        return []

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

    try:
        result = db.aggregation(Request, pipeline=pipeline)
    except ServerSelectionTimeoutError:
        return []

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
    try:
        result = db.aggregation(Request, pipeline=pipeline)
    except ServerSelectionTimeoutError:
        return []

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

    try:
        result = db.aggregation(Request, pipeline=pipeline)
    except ServerSelectionTimeoutError:
        return []

    if result is not None:
        return result

    # Can't find a result
    return []


def request_garden_send_latency_metrics(interval: int = 15):
    # Calculated the average trip down to a Target Garden from this Garden in seconds

    local_garden = config.get("garden.name")
    try:
        gardens = db.query(
            Garden, include_fields=["name"], filter_params={"name__ne": local_garden}
        )
    except Exception:
        gardens = []

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

        try:
            result = db.aggregation(Request, pipeline=pipeline)
        except ServerSelectionTimeoutError:
            return []

        if result is not None and len(result) > 0:
            total.append(
                {
                    "target_garden": garden.name,
                    "count": result[0]["count"],
                    "sum_value": result[0]["sum_value"],
                }
            )

    return total


def request_garden_return_latency_metrics(interval: int = 15):
    # Calculates the average trip from a Target Garden to this Garden in seconds

    local_garden = config.get("garden.name")
    try:
        gardens = db.query(
            Garden, include_fields=["name"], filter_params={"name__ne": local_garden}
        )
    except Exception:
        gardens = []

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
        try:
            result = db.aggregation(Request, pipeline=pipeline)
        except ServerSelectionTimeoutError:
            return []

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
            partial(request_garden_return_latency_metrics),
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


if __name__ == "__main__":
    logger.info("Running metrics server on port 8001")
    start_http_server(8001)

    setup_metrics()

    try:
        while True:
            time.sleep(15)
    except KeyboardInterrupt:
        logger.info("Shutting down")
