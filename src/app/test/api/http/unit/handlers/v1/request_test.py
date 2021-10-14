# -*- coding: utf-8 -*-
import json

import pytest
import tornado.web
from box import Box
from mongoengine import connect
from mongomock.gridfs import enable_gridfs_integration

import beer_garden.events
import beer_garden.requests
import beer_garden.router
from beer_garden import config
from beer_garden.api.http.client import SerializeHelper
from beer_garden.api.http.handlers.v1.request import RequestListAPI
from beer_garden.db.mongo.models import Garden, RawFile, System

enable_gridfs_integration()

# TODO: Load this from conftest using the actual _setup_application call
application = tornado.web.Application(
    [
        (r"/api/v1/requests/?", RequestListAPI),
    ],
    client=SerializeHelper(),
)


def format_form_data(metadata: list, data: str, boundary: str):
    form_data = "\r\n"

    for item in metadata:
        form_data += f"{item}\r\n"

    form_data += f"\r\n{data}"
    form_data += f"\r\n--{boundary}"

    return form_data


@pytest.fixture
def app():
    return application


@pytest.fixture(autouse=True)
def app_config(monkeypatch):
    app_config = Box(
        {
            "auth": {"enabled": False, "token_secret": "keepitsecret"},
            "garden": {"name": "somegarden"},
        }
    )
    monkeypatch.setattr(config, "_CONFIG", app_config)

    yield app_config


@pytest.fixture(autouse=True)
def common_mocks(monkeypatch, test_remote_system):
    def mock_determine_target(operation):
        return test_remote_system.namespace

    def mock_validate(request):
        return request

    def generic_mock(*args, **kwargs):
        pass

    monkeypatch.setattr(beer_garden.events, "publish", generic_mock)
    monkeypatch.setattr(beer_garden.requests, "_publish_request", generic_mock)
    monkeypatch.setattr(beer_garden.requests, "_validate_request", mock_validate)
    monkeypatch.setattr(beer_garden.router, "_determine_target", mock_determine_target)
    monkeypatch.setattr(beer_garden.router, "forward", generic_mock)


@pytest.fixture(autouse=True)
def db_cleanup():
    yield
    RawFile.drop_collection()


@pytest.fixture
def test_local_garden():
    garden = Garden(name="somegarden", connection_type="LOCAL").save()

    yield garden
    garden.delete()


@pytest.fixture
def test_remote_garden():
    garden = Garden(name="remotegarden", connection_type="HTTP").save()

    yield garden
    garden.delete()


@pytest.fixture
def test_local_system(test_local_garden):
    system = System(
        name="somesystem", version="1.0.0", namespace=test_local_garden.name
    ).save()

    yield system
    system.delete()


@pytest.fixture
def test_remote_system(test_remote_garden):
    system = System(
        name="somesystem", version="1.0.0", namespace=test_remote_garden.name
    ).save()

    yield system
    system.delete()


def generate_form_data(system) -> dict:
    boundary = "longuuidlikething"
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}

    request_parameter = {
        "system": system.name,
        "system_version": system.version,
        "namespace": system.namespace,
        "command": "mycommand",
        "instance_name": "default",
        "parameters": {"this": "doesntmatter"},
    }

    body = f"--{boundary}"
    body += format_form_data(
        ['Content-Disposition: form-data; name="request"'],
        json.dumps(request_parameter),
        boundary,
    )

    body += format_form_data(
        [
            'Content-Disposition: form-data; name="myfile"; filename="testfile.txt"',
            "Content-Type: text/plain",
        ],
        "a very witty example of plaintext",
        boundary,
    )

    body += "--\r\n"

    return {"headers": headers, "body": body}


class TestRequestListAPI:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.mark.gen_test
    def test_post_file_parameter_stores_as_raw_file_on_local_garden(
        self,
        http_client,
        app_config,
        base_url,
        test_local_system,
    ):
        url = f"{base_url}/api/v1/requests"
        form_data = generate_form_data(test_local_system)
        headers = form_data["headers"]
        body = form_data["body"]

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=body
        )
        response_body = json.loads(response.body.decode("utf-8"))
        file_id = response_body["parameters"]["myfile"]["id"]

        assert response.code == 201
        assert file_id is not None
        assert RawFile.objects.get(id=file_id) is not None

    @pytest.mark.gen_test
    def test_post_file_parameter_removes_base64_for_remote_garden(
        self,
        monkeypatch,
        http_client,
        app_config,
        base_url,
        test_remote_system,
        test_local_garden,
    ):
        url = f"{base_url}/api/v1/requests"
        form_data = generate_form_data(test_remote_system)
        headers = form_data["headers"]
        body = form_data["body"]

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=body
        )
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 201
        assert response_body["parameters"]["myfile"].get("id") is None
        assert response_body["parameters"]["myfile"].get("base64") is None
        assert len(RawFile.objects.all()) == 0
