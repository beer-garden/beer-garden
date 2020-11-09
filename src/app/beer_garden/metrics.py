# -*- coding: utf-8 -*-
""" Metrics Service

The metrics service manages:
* Connectivity to the Prometheus Server
* Creating default summary views in Prometheus
* Publishing `Request` metrics
"""

import datetime
import logging
from http.server import ThreadingHTTPServer

from brewtils.models import Request
from brewtils.stoppable_thread import StoppableThread
from prometheus_client import Gauge, Counter, Summary
from prometheus_client.exposition import MetricsHandler
from prometheus_client.registry import REGISTRY

import beer_garden.db.api as db


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
        self.logger.info("Initializing metric counts")
        initialize_counts()

        self.logger.info(f"Starting {self.display_name} on {self._host}:{self._port}")
        self.httpd.serve_forever()

        self.logger.info(f"{self.display_name} is stopped")

    def stop(self):
        self.httpd.shutdown()


# Summaries:
plugin_command_latency = Summary(
    "bg_plugin_command_latency_seconds",
    "Total time taken for a command to complete in seconds.",
    ["system", "instance_name", "system_version", "command", "status"],
)

# Counters:
completed_request_counter = Counter(
    "bg_completed_requests_total",
    "Number of completed requests.",
    ["system", "instance_name", "system_version", "command", "status"],
)
request_counter_total = Counter(
    "bg_requests_total",
    "Number of requests.",
    ["system", "instance_name", "system_version", "command"],
)

# Gauges:
queued_request_gauge = Gauge(
    "bg_queued_requests",
    "Number of requests waiting to be processed.",
    ["system", "instance_name", "system_version"],
)
in_progress_request_gauge = Gauge(
    "bg_in_progress_requests",
    "Number of requests IN_PROGRESS",
    ["system", "instance_name", "system_version"],
)


def request_latency(start_time):
    """Measure request latency in seconds as a float."""
    return (datetime.datetime.utcnow() - start_time).total_seconds()


def initialize_counts():
    requests = db.query(
        Request, filter_params={"status__in": ["CREATED", "IN_PROGRESS"]}
    )
    for request in requests:
        label_args = {
            "system": request.system,
            "system_version": request.system_version,
            "instance_name": request.instance_name,
        }

        if request.status == "CREATED":
            queued_request_gauge.labels(**label_args).inc()
        elif request.status == "IN_PROGRESS":
            in_progress_request_gauge.labels(**label_args).inc()


def request_created(request):
    queued_request_gauge.labels(
        system=request.system,
        system_version=request.system_version,
        instance_name=request.instance_name,
    ).inc()
    request_counter_total.labels(
        system=request.system,
        system_version=request.system_version,
        instance_name=request.instance_name,
        command=request.command,
    ).inc()


def request_started(request):
    """Update metrics associated with a Request update

    This call should happen after the save to the database.

    """
    labels = {
        "system": request.system,
        "system_version": request.system_version,
        "instance_name": request.instance_name,
    }

    queued_request_gauge.labels(**labels).dec()
    in_progress_request_gauge.labels(**labels).inc()


def request_completed(request):
    """Update metrics associated with a Request update

    This call should happen after the save to the database.

    """
    labels = {
        "system": request.system,
        "system_version": request.system_version,
        "instance_name": request.instance_name,
    }

    in_progress_request_gauge.labels(**labels).dec()

    latency = request_latency(request.created_at)
    labels["command"] = request.command
    labels["status"] = request.status

    completed_request_counter.labels(**labels).inc()
    plugin_command_latency.labels(**labels).observe(latency)
