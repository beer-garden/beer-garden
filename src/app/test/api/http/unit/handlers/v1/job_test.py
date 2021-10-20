# -*- coding: utf-8 -*-
import pytest

from mongoengine import connect
from beer_garden.db.mongo.models import Job
from brewtils.models import DateTrigger

from .. import TestHandlerBase

@pytest.fixture
def job():
    job = Job(trigger=DateTrigger())
    job.save()

    yield job
    job.delete()

class TestJobExecutionAPI:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.mark.gen_test
    def test_execute(self, http_client, base_url, job):
        url = f"{base_url}/api/v1/jobs/{job.id}/execute"
        body = ""

        response = yield http_client.fetch(url, method="POST", body=body)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200

    @pytest.mark.gen_test
    def test_execute_job_not_found(self, http_client, base_url):
        job_id = "not_real"
        url = f"{base_url}/api/v1/jobs/{job_id}/execute"
        body = ""

        response = yield http_client.fetch(url, method="POST", body=body)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
