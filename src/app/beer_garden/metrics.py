# -*- coding: utf-8 -*-
""" Metrics Service

The metrics service manages:
* Connectivity to the Prometheus Server
* Creating default summary views in Prometheus
* Publishing `Request` metrics
"""

import datetime

from brewtils.models import Request
from prometheus_client import Counter, Gauge, Summary
from prometheus_client.exposition import generate_latest
from prometheus_client.registry import REGISTRY

import beer_garden.db.api as db


def get_metrics():
    return generate_latest(REGISTRY)


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
canceled_request_counter = Counter(
    "bg_canceled_requests_total",
    "Number of canceled requests.",
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

def request_canceled(request):
    """Update metrics associated with a Request canceled

    This call should happen after the save to the database.

    """
    labels = {
        "system": request.system,
        "system_version": request.system_version,
        "instance_name": request.instance_name,
    }

    canceled_request_counter.labels(**labels).inc()
