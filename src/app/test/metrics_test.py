# -*- coding: utf-8 -*-
from datetime import datetime
from time import sleep

import pytest
from mock import Mock

import beer_garden.metrics as metrics


@pytest.fixture
def prometheus_mocks(monkeypatch):
    # TODO - Test http api latency
    # monkeypatch.setattr(metrics, "http_api_latency_total", Mock())
    monkeypatch.setattr(metrics, "plugin_command_latency", Mock())
    monkeypatch.setattr(metrics, "completed_request_counter", Mock())
    monkeypatch.setattr(metrics, "request_counter_total", Mock())
    monkeypatch.setattr(metrics, "queued_request_gauge", Mock())
    monkeypatch.setattr(metrics, "in_progress_request_gauge", Mock())


class TestMetrics(object):
    @pytest.mark.parametrize("wait", [0, 0.1, 0.25])
    def test_request_latency(self, wait):
        now = datetime.utcnow()
        sleep(wait)
        latency = metrics.request_latency(now)
        assert 0.01 > latency - wait

    @pytest.mark.parametrize(
        "status,queued,in_progress",
        [("CREATED", 1, 0), ("IN_PROGRESS", 0, 1), ("SUCCESS", 0, 0)],
    )
    def test_initialize_counts(
        self, prometheus_mocks, monkeypatch, bg_request, status, queued, in_progress
    ):
        bg_request.status = status

        monkeypatch.setattr(metrics.db, "query", Mock(return_value=[bg_request]))

        metrics.initialize_counts()
        assert queued == metrics.queued_request_gauge.labels.return_value.inc.call_count
        assert (
            in_progress
            == metrics.in_progress_request_gauge.labels.return_value.inc.call_count
        )

    def test_request_created(self, prometheus_mocks, bg_request):
        metrics.request_created(bg_request)

        metrics.queued_request_gauge.labels.assert_called_once_with(
            system=bg_request.system,
            system_version=bg_request.system_version,
            instance_name=bg_request.instance_name,
        )
        assert metrics.queued_request_gauge.labels.return_value.inc.call_count == 1

        metrics.request_counter_total.labels.assert_called_once_with(
            system=bg_request.system,
            system_version=bg_request.system_version,
            instance_name=bg_request.instance_name,
            command=bg_request.command,
        )
        assert metrics.request_counter_total.labels.return_value.inc.call_count == 1

    def test_request_started(self, prometheus_mocks, bg_request):
        metrics.request_started(bg_request)

        metrics.queued_request_gauge.labels.assert_called_once_with(
            system=bg_request.system,
            system_version=bg_request.system_version,
            instance_name=bg_request.instance_name,
        )
        assert metrics.queued_request_gauge.labels.return_value.dec.call_count == 1

        metrics.in_progress_request_gauge.labels.assert_called_once_with(
            system=bg_request.system,
            system_version=bg_request.system_version,
            instance_name=bg_request.instance_name,
        )
        assert metrics.in_progress_request_gauge.labels.return_value.inc.call_count == 1

    def test_request_completed(self, prometheus_mocks, bg_request):
        metrics.request_completed(bg_request)

        metrics.in_progress_request_gauge.labels.assert_called_once_with(
            system=bg_request.system,
            system_version=bg_request.system_version,
            instance_name=bg_request.instance_name,
        )
        assert metrics.in_progress_request_gauge.labels.return_value.dec.call_count == 1

        metrics.completed_request_counter.labels.assert_called_once_with(
            system=bg_request.system,
            system_version=bg_request.system_version,
            instance_name=bg_request.instance_name,
            command=bg_request.command,
            status=bg_request.status,
        )
        assert metrics.completed_request_counter.labels.return_value.inc.call_count == 1

        metrics.plugin_command_latency.labels.assert_called_once_with(
            system=bg_request.system,
            system_version=bg_request.system_version,
            instance_name=bg_request.instance_name,
            command=bg_request.command,
            status=bg_request.status,
        )
        assert (
            metrics.plugin_command_latency.labels.return_value.observe.call_count == 1
        )
