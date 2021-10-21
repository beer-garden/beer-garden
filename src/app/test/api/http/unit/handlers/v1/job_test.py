# -*- coding: utf-8 -*-
import pytest
import tornado.web
from mock import Mock

from beer_garden.api.http.handlers.v1.job import JobExecutionAPI

from tornado.httpclient import HTTPClientError

# TODO: Load this from conftest using the actual _setup_application call
application = tornado.web.Application(
    [
        (r"/api/v1/jobs/(\w+)/execute/?", JobExecutionAPI),
    ]
)


@pytest.fixture()
def app():
    return application


class TestJobExecutionAPI:
    @pytest.mark.gen_test
    def test_execute(self, app, base_url, http_client, monkeypatch, bg_job):
        monkeypatch.setattr(
            beer_garden.scheduler, "execute_job", Mock(return_value=bg_job)
        )
        job_id = "real_id"
        url = f"{base_url}/api/v1/jobs/{job_id}/execute"
        body = ""

        response = yield http_client.fetch(url, method="POST", body=body)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200

    @pytest.mark.gen_test
    def test_execute_job_not_found(self, http_client, base_url):
        job_id = "not_real"
        url = f"{base_url}/api/v1/jobs/{job_id}/execute"
        body = ""

        # 404 error
        with pytest.raises(HTTPClientError):
            response = yield http_client.fetch(url, method="POST", body=body)
