import pytest
from datetime import datetime
from mock import Mock
from time import sleep

import brew_view.metrics as metrics


@pytest.fixture
def prometheus_mocks(monkeypatch):
    monkeypatch.setattr(metrics, 'http_api_latency_total', Mock())
    monkeypatch.setattr(metrics, 'plugin_command_latency', Mock())
    monkeypatch.setattr(metrics, 'completed_request_counter', Mock())
    monkeypatch.setattr(metrics, 'request_counter_total', Mock())
    monkeypatch.setattr(metrics, 'queued_request_gauge', Mock())
    monkeypatch.setattr(metrics, 'in_progress_request_gauge', Mock())


class TestMetrics(object):

    @pytest.mark.parametrize('wait', [0, 0.1, 0.25])
    def test_request_latency(self, wait):
        now = datetime.utcnow()
        sleep(wait)
        latency = metrics.request_latency(now)
        assert 0.01 > latency - wait

    @pytest.mark.parametrize('status,queued,in_progress', [
        ('CREATED', 1, 0),
        ('IN_PROGRESS', 0, 1),
        ('SUCCESS', 0, 0),
    ])
    def test_initialize_counts(
            self,
            prometheus_mocks,
            monkeypatch,
            bg_request,
            status,
            queued,
            in_progress,
    ):
        bg_request.status = status

        requests_mock = Mock()
        requests_mock.objects.return_value = [bg_request]
        monkeypatch.setattr(metrics, 'Request', requests_mock)

        metrics.initialize_counts()
        assert queued == metrics.queued_request_gauge.labels.return_value.inc.call_count
        assert in_progress == metrics.in_progress_request_gauge.labels.return_value.inc.call_count

    def test_request_created(self, prometheus_mocks, bg_request):
        metrics.request_created(bg_request)

        metrics.queued_request_gauge.labels.assert_called_once_with(
            system=bg_request.system,
            system_version=bg_request.system_version,
            instance_name=bg_request.instance_name,
        )
        assert 1 == metrics.queued_request_gauge.labels.return_value.inc.call_count

        metrics.request_counter_total.labels.assert_called_once_with(
            system=bg_request.system,
            system_version=bg_request.system_version,
            instance_name=bg_request.instance_name,
            command=bg_request.command,
        )
        assert 1 == metrics.request_counter_total.labels.return_value.inc.call_count

    @pytest.mark.parametrize('status,old_status,label,inc', [
        ('IN_PROGRESS', 'CREATED', 'queued_request_gauge', False),
        ('IN_PROGRESS', 'CREATED', 'in_progress_request_gauge', True),
        ('SUCCESS', 'IN_PROGRESS', 'in_progress_request_gauge', False),
        ('SUCCESS', 'IN_PROGRESS', 'completed_request_counter', True),
    ])
    def test_request_updated(
            self, prometheus_mocks, bg_request, status, old_status, label, inc):
        bg_request.status = status
        metrics.request_updated(bg_request, old_status)

        label_mock = getattr(metrics, label)

        if inc:
            assert label_mock.labels.return_value.inc.called is True
        else:
            assert label_mock.labels.return_value.dec.called is True
