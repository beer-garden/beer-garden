# -*- coding: utf-8 -*-
import json

import pytest
import tornado.web
from box import Box
from mongoengine import connect

from beer_garden import config
from beer_garden.api.http.client import SerializeHelper
from beer_garden.api.http.handlers.v1.job import JobExecutionAPI
from beer_garden.db.mongo.api import from_brewtils

from tornado.httpclient import HTTPClientError


application = tornado.web.Application(
    [
        (r"/api/v1/jobs/(\w+)/execute/?", JobExecutionAPI),
    ],
    client=SerializeHelper(),
)


@pytest.fixture(autouse=True)
def app_config(monkeypatch):
    app_config = Box(
        {
            "garden": {"name": "somegarden"},
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)

    yield app_config


@pytest.fixture
def scheduled_job_id(bg_job):
    job = from_brewtils(bg_job)
    job.save()

    yield job.id
    job.delete()


@pytest.fixture
def app():
    return application


class TestJobExecutionAPI:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.mark.gen_test
    def test_execute(self, base_url, http_client, monkeypatch, scheduled_job_id):
        url = f"{base_url}/api/v1/jobs/{scheduled_job_id}/execute"
        body = ""

        response = yield http_client.fetch(url, method="POST", body=body)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 201

    @pytest.mark.gen_test
    def test_execute_job_not_found(self, http_client, base_url):
        job_id = "not_real"
        url = f"{base_url}/api/v1/jobs/{job_id}/execute"
        body = ""

        # 404 error
        with pytest.raises(HTTPClientError):
            response = yield http_client.fetch(url, method="POST", body=body)
