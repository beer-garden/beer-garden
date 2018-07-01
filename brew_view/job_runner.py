# -*- coding: utf-8 -*-
import brew_view
from brewtils.rest.easy_client import EasyClient

easy_client = EasyClient(bg_host='localhost', bg_port=2337, **brew_view.config.web)


def run_job(request_payload):
    request = construct_request(request_payload)
    easy_client.create_request(request)


# TODO: Actually construct a request from the payload.
def construct_request(payload):
    return {
        'system': 'echo',
        'system_version': '1.0.0.dev0',
        'instance_name': 'default',
        'command': 'say',
        'parameters': {
            'message': 'jaksdlfjkasldjfklsadf'
        }
    }
