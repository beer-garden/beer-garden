# -*- coding: utf-8 -*-s
from functools import partial

import pytest
from brewtils.models import Garden
from mock import Mock

import beer_garden.db.api as db
import beer_garden.metrics as metrics
from beer_garden import config


@pytest.fixture
def request_aggregation(monkeypatch):
    aggregation_mock = Mock()
    monkeypatch.setattr(db, "aggregation", aggregation_mock)
    return aggregation_mock


@pytest.fixture
def get_gardens_mock(monkeypatch):
    gardens_mock = Mock()
    monkeypatch.setattr(metrics, "get_gardens", gardens_mock)
    return gardens_mock


@pytest.fixture
def garden_get_gardens():
    gardens = [Garden(name="downstream")]
    yield gardens


@pytest.fixture
def request_garden_totals():
    totals = [
        {
            "namespace": "default",
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "command": "say",
            "target_garden": "default",
            "count": 2,
        }
    ]
    yield totals


@pytest.fixture
def request_garden_completed_totals():
    totals = [
        {
            "namespace": "default",
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "command": "say",
            "status": "SUCCESS",
            "target_garden": "default",
            "count": 3,
        }
    ]
    yield totals


@pytest.fixture
def request_garden_status_totals():
    totals = [
        {
            "namespace": "default",
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "target_garden": "default",
            "count": 5,
        }
    ]
    yield totals


@pytest.fixture
def request_garden_plugin_command_latency_metrics():
    metrics = [
        {
            "namespace": "default",
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "command": "say",
            "status": "SUCCESS",
            "target_garden": "default",
            "count": 10,
            "sum_value": 20,
        }
    ]
    yield metrics


@pytest.fixture
def request_garden_send_latency_metrics():
    metrics = [{"target_garden": "downstream", "count": 1, "sum_value": 0.161}]
    yield metrics


@pytest.fixture
def request_garden_return_latency_metrics():
    metrics = [{"target_garden": "downstream", "count": 1, "sum_value": 0.96}]
    yield metrics


class TestMetrics(object):
    @classmethod
    def setup_class(cls):
        config._CONFIG = {"garden": {"name": "localgarden"}}

    # Test request_garden_totals
    def test_request_garden_totals(
        monkeypatch, request_aggregation, request_garden_totals
    ):

        request_aggregation.return_value = request_garden_totals

        result = metrics.request_garden_totals()
        assert result == request_garden_totals

        collector = metrics.CumulativeCollector(
            partial(metrics.request_garden_totals),
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

        collect = list(collector.collect())

        assert len(collect) == 1
        metric_family = collect[0]

        assert metric_family.type == "gauge"
        assert metric_family.name == "bg_requests_total"

        samples = metric_family.samples
        assert len(samples) == 1

        sample_value = samples[0]
        assert sample_value.labels == {
            "namespace": "default",
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "command": "say",
            "target_garden": "default",
        }
        assert sample_value.value == 2

    def test_request_garden_completed_totals(
        monkeypatch, request_aggregation, request_garden_completed_totals
    ):
        request_aggregation.return_value = request_garden_completed_totals

        result = metrics.request_garden_completed_totals()
        assert result == request_garden_completed_totals

        collector = metrics.CumulativeCollector(
            partial(metrics.request_garden_completed_totals),
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

        collect = list(collector.collect())

        assert len(collect) == 1
        metric_family = collect[0]

        assert metric_family.type == "gauge"
        assert metric_family.name == "bg_completed_requests_total"

        samples = metric_family.samples
        assert len(samples) == 1

        sample_value = samples[0]
        assert sample_value.labels == {
            "namespace": "default",
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "command": "say",
            "status": "SUCCESS",
            "target_garden": "default",
        }
        assert sample_value.value == 3

    def test_request_garden_status_totals(
        monkeypatch, request_aggregation, request_garden_status_totals
    ):
        request_aggregation.return_value = request_garden_status_totals

        result = metrics.request_garden_status_metrics(["IN_PROGRESS"])
        assert result == request_garden_status_totals

        collector = metrics.TimeWindowCollector(
            partial(metrics.request_garden_status_metrics, ["IN_PROGRESS"]),
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

        collect = list(collector.collect())

        assert len(collect) == 1
        metric_family = collect[0]

        assert metric_family.type == "gauge"
        assert metric_family.name == "bg_in_progress_requests"

        samples = metric_family.samples
        assert len(samples) == 1

        sample_value = samples[0]
        assert sample_value.labels == {
            "namespace": "default",
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "target_garden": "default",
        }
        assert sample_value.value == 5

    def test_request_garden_plugin_command_latency_metrics(
        monkeypatch, request_aggregation, request_garden_plugin_command_latency_metrics
    ):
        request_aggregation.return_value = request_garden_plugin_command_latency_metrics

        result = metrics.request_garden_plugin_command_latency_metrics()
        assert result == request_garden_plugin_command_latency_metrics

        collector = metrics.SummaryCollector(
            partial(metrics.request_garden_plugin_command_latency_metrics),
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

        collect = list(collector.collect())

        assert len(collect) == 1
        metric_family = collect[0]

        assert metric_family.type == "summary"
        assert metric_family.name == "bg_plugin_command_latency_seconds"

        samples = metric_family.samples
        assert len(samples) == 2

        count = samples[0]
        assert count.labels == {
            "namespace": "default",
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "command": "say",
            "status": "SUCCESS",
            "target_garden": "default",
        }
        assert count.value == 10

        sum_value = samples[1]
        assert sum_value.labels == {
            "namespace": "default",
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "command": "say",
            "status": "SUCCESS",
            "target_garden": "default",
        }
        assert sum_value.value == 20

    def test_request_garden_send_latency_metrics(
        monkeypatch,
        get_gardens_mock,
        garden_get_gardens,
        request_aggregation,
        request_garden_send_latency_metrics,
    ):
        get_gardens_mock.return_value = garden_get_gardens
        request_aggregation.return_value = request_garden_send_latency_metrics

        result = metrics.request_garden_send_latency_metrics()
        assert result == request_garden_send_latency_metrics

        collector = metrics.SummaryCollector(
            partial(metrics.request_garden_send_latency_metrics),
            name="bg_garden_send_latency",
            description="Total number of seconds garden is taking to send",
            labels=["target_garden"],
        )

        collect = list(collector.collect())

        assert len(collect) == 1
        metric_family = collect[0]

        assert metric_family.type == "summary"
        assert metric_family.name == "bg_garden_send_latency"

        samples = metric_family.samples
        assert len(samples) == 2

        count = samples[0]
        assert count.labels == {
            "target_garden": "downstream",
        }
        assert count.value == 1

        sum_value = samples[1]
        assert sum_value.labels == {
            "target_garden": "downstream",
        }
        assert sum_value.value == 0.161

    def test_request_garden_return_latency_metrics(
        monkeypatch,
        get_gardens_mock,
        garden_get_gardens,
        request_aggregation,
        request_garden_return_latency_metrics,
    ):
        get_gardens_mock.return_value = garden_get_gardens
        request_aggregation.return_value = request_garden_return_latency_metrics

        result = metrics.request_garden_return_latency_metrics()
        assert result == request_garden_return_latency_metrics

        collector = metrics.SummaryCollector(
            partial(metrics.request_garden_return_latency_metrics),
            name="bg_garden_return_latency",
            description="Total number of seconds each garden is taking to receive",
            labels=["target_garden"],
        )

        collect = list(collector.collect())

        assert len(collect) == 1
        metric_family = collect[0]

        assert metric_family.type == "summary"
        assert metric_family.name == "bg_garden_return_latency"

        samples = metric_family.samples
        assert len(samples) == 2

        count = samples[0]
        assert count.labels == {
            "target_garden": "downstream",
        }
        assert count.value == 1

        sum_value = samples[1]
        assert sum_value.labels == {
            "target_garden": "downstream",
        }
        assert sum_value.value == 0.96
