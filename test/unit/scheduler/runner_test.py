# -*- coding: utf-8 -*-
from mock import patch

from brew_view.scheduler.runner import run_job


def test_run_job(bg_request_template):
    with patch("brew_view.easy_client") as client_mock:
        run_job("job_id", bg_request_template)

    client_mock.create_request.assert_called_with(bg_request_template)
    assert bg_request_template.metadata["_bg_job_id"] == "job_id"
