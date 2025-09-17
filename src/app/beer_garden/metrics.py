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
from http.server import ThreadingHTTPServer

import elasticapm
from brewtils.models import BaseModel, Event, Operation, Request
from brewtils.stoppable_thread import StoppableThread
from elasticapm import Client
from elasticapm.metrics.base_metrics import MetricSet
from prometheus_client import Counter, Gauge, Summary
from prometheus_client.exposition import MetricsHandler
from prometheus_client.registry import REGISTRY

import beer_garden.config as config
import beer_garden.db.api as db
import beer_garden.events

logger = logging.getLogger(__name__)


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
    return (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()


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

        if isinstance(result, Operation):
            return extract_custom_context(result.model)
        if isinstance(result, Event):
            elasticapm.label(event_name=result.name)
            elasticapm.label(event_garden=result.garden)

            if hasattr(result, "payload"):
                return extract_custom_context(result.payload)
        elif isinstance(result, Request):
            if result.metadata:
                elasticapm.label(**result.metadata)

            # Helpful for trending sizes, but can be expensive to calculate
            if logger.level == logging.DEBUG:
                elasticapm.label(request_size=_calculate_size(result))
                if hasattr(result, "parameters"):
                    elasticapm.label(
                        request_parameter_size=_calculate_size(result.parameters)
                    )
                if hasattr(result, "output"):
                    elasticapm.label(request_output_size=_calculate_size(result.output))

        if hasattr(result, "id") and result.id:
            elasticapm.label(mongo_id=result.id)

        # Helpful for trending sizes, but can be expensive to calculate
        if logger.level == logging.DEBUG:
            elasticapm.label(result_size=_calculate_size(result))

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
