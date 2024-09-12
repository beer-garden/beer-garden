# -*- coding: utf-8 -*-
""" Metrics Service

The metrics service manages:
* Connectivity to the Prometheus Server
* Creating default summary views in Prometheus
* Publishing `Request` metrics
"""

import datetime
import logging
import re
from http.server import ThreadingHTTPServer

import elasticapm
import wrapt
from brewtils.models import Operation, Request
from brewtils.stoppable_thread import StoppableThread
from elasticapm import Client
from prometheus_client import Counter, Gauge, Summary
from prometheus_client.exposition import MetricsHandler
from prometheus_client.registry import REGISTRY

import beer_garden.config as config
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
        self.logger.debug("Initializing metric counts")
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


def initialize_elastic_client(label: str):
    """Initializes the Elastic APM client connection

    Args:
        label (str): Name of services being tracked
    """
    if config.get("metrics.elastic.enabled"):
        Client(
            {
                "SERVICE_NAME": (
                    f"{re.sub(r'[^a-zA-Z0-9 _-]', '', config.get('garden.name'))}"
                    f"-{label}"
                ),
                "ELASTIC_APM_SERVER_URL": config.get("metrics.elastic.url"),
            }
        )


def extract_custom_context(result) -> None:
    """Extracts values from models to be tracked in the custom context fields

    Args:
        result: Any object to be tracked
    """
    custom_context = {}

    if isinstance(result, Operation):
        if hasattr(result, "payload"):
            return extract_custom_context(result.payload)
    elif isinstance(result, Request):
        if result.metadata:
            for key, value in result.metadata.items():
                custom_context[key] = value
    if hasattr(result, "id"):
        custom_context["id"] = result.id

    if custom_context:
        elasticapm.set_custom_context(custom_context)


def collect_metrics(transaction_type: str = None, group: str = None):
    """Decorator that will result in the function being audited for metrics

    Args:
        transaction_type: Type of transaction that is being recorded
        group: Grouping label to prepend function name

    Raises:
        Any: If the underlying function raised an exception it will be re-raised

    Returns:
        Any: The wrapped function result
    """

    @wrapt.decorator
    def wrapper(wrapped, class_obj, args, kwargs):
        client = None

        if config.get("metrics.elastic.enabled"):
            if args and isinstance(args[0], Operation):
                transaction_label = args[0].operation_type
            elif group:
                transaction_label = f"{group} - {wrapped.__name__}"
            else:
                transaction_label = f"{wrapped.__name__}"

            client = elasticapm.get_client()
            if client:
                trace_id = elasticapm.get_trace_id()
                client.begin_transaction(
                    transaction_type=transaction_type,
                    trace_parent=trace_id if trace_id else elasticapm.get_span_id(),
                )
                elasticapm.set_transaction_name(transaction_label)

                if hasattr(class_obj, "get_current_user"):
                    current_user = class_obj.get_current_user()
                    if current_user:
                        elasticapm.set_user_context(
                            username=current_user.username, user_id=current_user.id
                        )

        try:
            result = wrapped(*args, **kwargs)

            if client:
                extract_custom_context(result)
                client.end_transaction(result="success")

            return result
        except Exception:

            if client:
                client.capture_exception()
                client.end_transaction(transaction_label, "failure")
            raise

    return wrapper
