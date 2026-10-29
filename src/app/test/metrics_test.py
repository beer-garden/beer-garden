# -*- coding: utf-8 -*-s
from functools import partial

import pytest
from mock import Mock

import beer_garden.metrics as metrics
from beer_garden import config


@pytest.fixture
def calculate_garden_statistics_mock(monkeypatch):
    calculate_garden_statistics_mock = Mock()
    monkeypatch.setattr(
        metrics, "calculate_garden_statistics", calculate_garden_statistics_mock
    )
    return calculate_garden_statistics_mock


@pytest.fixture
def garden_calculate_garden_statistics():
    stats = {
        "CPU_USAGE": 2.0,
        "CPU_BG_USAGE": 0.0,
        "MEM_TOTAL": 15.41,
        "MEM_USAGE": 5.7,
        "MEM_BG_USAGE": 0.09,
        "MEM_AVAILABLE": 9.71,
        "MEM_FREE": 5.96,
    }
    yield stats


@pytest.fixture
def garden_os_metrics():
    metrics = [
        {
            "CPU_BG_USAGE": 0.0,
            "CPU_USAGE": 2.0,
            "GARDEN_NAME": "localgarden",
            "MEM_AVAILABLE": 9.71,
            "MEM_BG_USAGE": 0.09,
            "MEM_FREE": 5.96,
            "MEM_TOTAL": 15.41,
            "MEM_USAGE": 5.7,
        }
    ]
    yield metrics


class TestMetrics(object):
    @classmethod
    def setup_class(cls):
        config._CONFIG = {"garden": {"name": "localgarden"}}

    def test_garden_os_metrics(
        monkeypatch,
        calculate_garden_statistics_mock,
        garden_calculate_garden_statistics,
        garden_os_metrics,
    ):
        calculate_garden_statistics_mock.return_value = (
            garden_calculate_garden_statistics
        )

        result = metrics.garden_os_metrics()
        assert result == garden_os_metrics

        collector = metrics.CumulativeCollector(
            partial(metrics.garden_os_metrics),
            name="bg_garden_os_metrics",
            description="Garden OS Metrics CPU/MEM",
            labels=["GARDEN_NAME"],
            metric_keys=[
                "CPU_USAGE",
                "CPU_BG_USAGE",
                "MEM_TOTAL",
                "MEM_USAGE",
                "MEM_BG_USAGE",
                "MEM_AVAILABLE",
                "MEM_FREE",
            ],
        )

        collect = list(collector.collect())

        assert len(collect) == 1
        metric_family = collect[0]

        assert metric_family.type == "gauge"
        assert metric_family.name == "bg_garden_os_metrics"

        samples = metric_family.samples
        assert len(samples) == 7

        sample_value = samples[0]
        assert sample_value.labels == {
            "GARDEN_NAME": "localgarden",
            "METRIC": "CPU_USAGE",
        }
        assert sample_value.value == 2.0
