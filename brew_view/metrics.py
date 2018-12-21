import datetime
from prometheus_client import Gauge, Counter, Summary

from bg_utils.mongo.models import Request
from brewtils.models import Request as BrewtilsRequest

# Summaries:
http_api_latency_total = Summary(
    "bg_http_api_latency_seconds",
    "Total number of seconds each API endpoint is taking to respond.",
    ["method", "route", "status"],
)
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
    for request in Request.objects(status__in=["CREATED", "IN_PROGRESS"]):
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


def request_updated(request, status_before):
    """Update metrics associated with a Request update

    This call should happen after the save to the database.

    """
    if (
        status_before == request.status
        or status_before in BrewtilsRequest.COMPLETED_STATUSES
    ):
        return

    labels = {
        "system": request.system,
        "system_version": request.system_version,
        "instance_name": request.instance_name,
    }

    if status_before == "CREATED":
        queued_request_gauge.labels(**labels).dec()
    elif status_before == "IN_PROGRESS":
        in_progress_request_gauge.labels(**labels).dec()

    if request.status == "IN_PROGRESS":
        in_progress_request_gauge.labels(**labels).inc()

    elif request.status in BrewtilsRequest.COMPLETED_STATUSES:
        latency = request_latency(request.created_at)
        labels["command"] = request.command
        labels["status"] = request.status

        completed_request_counter.labels(**labels).inc()
        plugin_command_latency.labels(**labels).observe(latency)
