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
system_created_counter = Counter(
    "bg_system_created_total",
    "Number of times system created",
    [
        "system",
        "system_version",
    ],
)
system_removed_counter = Counter(
    "bg_system_removed_total",
    "Number of times system removed",
    [
        "system",
        "system_version",
    ],
)
system_updated_counter = Counter(
    "bg_system_updated_total",
    "Number of times system updated",
    [
        "system",
        "system_version",
    ],
)
instance_initialized_counter = Counter(
    "bg_instance_initialized_total",
    "Number of times instance initialized",
    [
        "instance_name",
        "system",
        "system_version",
    ],
)
instance_started_counter = Counter(
    "bg_instance_started_total",
    "Number of times instance started",
    [
        "instance_name",
        "system",
        "system_version",
    ],
)
instance_stopped_counter = Counter(
    "bg_instance_stopped_total",
    "Number of times instance stopped",
    [
        "instance_name",
        "system",
        "system_version",
    ],
)
instance_updated_counter = Counter(
    "bg_instance_updated_total",
    "Number of times instance updated",
    [
        "instance_name",
        "system",
        "system_version",
    ],
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


def system_created(system):
    """Update plugin started metric"""
    labels = {
        "system": system.name,
        "system_version": system.version,
    }
    system_created_counter.labels(**labels).inc()


def system_removed(system):
    """
    Update plugin stopped metric
    """
    labels = {
        "system": system.name,
        "system_version": system.version,
    }
    system_removed_counter.labels(**labels).inc()


def system_updated(system):
    """
    Update plugin stopped metric
    """
    labels = {
        "system": system.name,
        "system_version": system.version,
    }
    system_updated_counter.labels(**labels).inc()


def instance_started(instance, system):
    """Update plugin started metric"""
    labels = {
        "instance_name": instance.name,
        "system": system.name,
        "system_version": system.version,
    }
    instance_started_counter.labels(**labels).inc()


def instance_stopped(instance, system):
    """
    Update plugin stopped metric
    """
    labels = {
        "instance_name": instance.name,
        "system": system.name,
        "system_version": system.version,
    }
    instance_stopped_counter.labels(**labels).inc()


def instance_updated(instance, system):
    """
    Update plugin stopped metric
    """
    labels = {
        "instance_name": instance.name,
        "system": system.name,
        "system_version": system.version,
    }
    instance_updated_counter.labels(**labels).inc()


def instance_initialized(instance, system):
    """
    Update plugin stopped metric
    """
    labels = {
        "instance_name": instance.name,
        "system": system.name,
        "system_version": system.version,
    }
    instance_initialized_counter.labels(**labels).inc()
