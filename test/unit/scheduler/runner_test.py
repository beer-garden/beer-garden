# -*- coding: utf-8 -*-
from mock import patch

from brew_view.scheduler.runner import run_job


def test_run_job():
    with patch('brew_view.easy_client') as client_mock:
        run_job('request_template')

    client_mock.create_request.assert_called_with('request_template')
