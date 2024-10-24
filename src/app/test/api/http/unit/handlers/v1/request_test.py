# -*- coding: utf-8 -*-
import json

import pytest
from brewtils.models import Role, User
from mongomock.gridfs import enable_gridfs_integration
from tornado.httpclient import HTTPError, HTTPRequest

import beer_garden.db.mongo.models
import beer_garden.events
import beer_garden.requests
import beer_garden.router
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import Garden, RawFile, Request, System
from beer_garden.role import create_role, delete_role
from beer_garden.user import create_user, delete_user

enable_gridfs_integration()


def format_form_data(metadata: list, data: str, boundary: str):
    form_data = "\r\n"

    for item in metadata:
        form_data += f"{item}\r\n"

    form_data += f"\r\n{data}"
    form_data += f"\r\n--{boundary}"

    return form_data


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


@pytest.fixture(autouse=True)
def common_mocks(monkeypatch, local_system):
    def mock_determine_target(operation):
        return local_system.namespace

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
    Request.drop_collection()


@pytest.fixture(autouse=True)
def local_system():
    system = System(
        name="somesystem", version="1.0.0", namespace="somegarden", local=True
    ).save()

    yield system
    system.delete()


@pytest.fixture(autouse=True)
def remote_system():
    system = System(
        name="somesystem", version="1.0.0", namespace="remotegarden", local=False
    ).save()

    yield system
    system.delete()


@pytest.fixture(autouse=True)
def remote_garden(remote_system):
    garden = Garden(
        name="remotegarden",
        connection_type="HTTP",
        has_parent=True,
        systems=[remote_system],
    ).save()

    yield garden
    garden.delete()


@pytest.fixture(autouse=True)
def local_garden(local_system, remote_garden):
    garden = Garden(
        name="somegarden",
        connection_type="LOCAL",
        children=[remote_garden],
        systems=[local_system],
    ).save()

    yield garden
    garden.delete()


@pytest.fixture(autouse=True)
def request_permitted(remote_system):
    request = Request(
        system=remote_system.name,
        system_version=remote_system.version,
        namespace=remote_system.namespace,
        command="mycommand",
        instance_name="default",
        parameters={"this": "doesntmatter"},
    )
    request.save()

    yield request
    request.delete()


@pytest.fixture(autouse=True)
def request_not_permitted(local_system):
    request = Request(
        system=local_system.name,
        system_version=local_system.version,
        namespace=local_system.namespace,
        command="mycommand",
        instance_name="default",
        parameters={"this": "doesntmatter"},
    )
    request.save()

    yield request
    request.delete()


@pytest.fixture
def request_permitted_child(remote_system, request_permitted):
    request = Request(
        system=remote_system.name,
        system_version=remote_system.version,
        namespace=remote_system.namespace,
        command="mycommand",
        instance_name="default",
        parameters={"im": "thechild"},
        parent=request_permitted,
    )
    request.save()

    yield request
    request.delete()


def _gridfs_output():
    return "large_output_stored_in_gridfs"


@pytest.fixture
def request_with_gridfs_output(monkeypatch, local_system):
    monkeypatch.setattr(beer_garden.db.mongo.models, "REQUEST_MAX_PARAM_SIZE", 0)

    request = Request(
        system=local_system.name,
        system_version=local_system.version,
        namespace=local_system.namespace,
        command="mycommand",
        instance_name="default",
        parameters={"this": "doesntmatter"},
        status="SUCCESS",
        output=_gridfs_output(),
    )
    request.save()

    yield request
    request.delete()


@pytest.fixture
def operator_role(request_permitted):
    role = create_role(
        Role(
            name="operator",
            permission="OPERATOR",
            scope_systems=[request_permitted.system],
            scope_namespaces=[request_permitted.namespace],
        )
    )
    yield role
    delete_role(role)


@pytest.fixture
def user(operator_role):
    user = create_user(User(username="testuser", local_roles=[operator_role]))
    yield user
    delete_user(user=user)


@pytest.fixture
def access_token(user):
    yield issue_token_pair(user)["access"]


class TestRequestAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_returns_any_request(
        self, http_client, base_url, request_not_permitted
    ):
        url = f"{base_url}/api/v1/requests/{request_not_permitted.id}"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == str(request_not_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_returns_permitted_request(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        request_permitted,
    ):
        url = f"{base_url}/api/v1/requests/{request_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == str(request_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_returns_403_for_not_permitted_request(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        request_not_permitted,
    ):
        url = f"{base_url}/api/v1/requests/{request_not_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    def test_auth_enabled_allows_patch_for_permitted_request(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        request_permitted,
    ):
        url = f"{base_url}/api/v1/requests/{request_permitted.id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        patch_body = [
            {"operation": "replace", "path": "/status", "value": "IN_PROGRESS"}
        ]
        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 200
        assert Request.objects.get(id=request_permitted.id).status == "IN_PROGRESS"

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_patch_for_not_permitted_request(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        request_not_permitted,
    ):
        url = f"{base_url}/api/v1/requests/{request_not_permitted.id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        patch_body = [
            {"operation": "replace", "path": "/status", "value": "IN_PROGRESS"}
        ]
        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert (
            Request.objects.get(id=request_not_permitted.id).status
            == request_not_permitted.status
        )

    @pytest.mark.gen_test
    def test_get_populates_children_when_present(
        self, http_client, base_url, request_permitted, request_permitted_child
    ):
        url = f"{base_url}/api/v1/requests/{request_permitted.id}"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["children"] is not None
        assert response_body["children"][0]["id"] == str(request_permitted_child.id)

    @pytest.mark.gen_test
    def test_get_populates_output_from_gridfs(
        self, http_client, base_url, request_with_gridfs_output
    ):
        url = f"{base_url}/api/v1/requests/{request_with_gridfs_output.id}"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        # Verify data is setup correctly (output got stored in gridfs)
        assert request_with_gridfs_output.output is None
        assert request_with_gridfs_output.output_gridfs is not None

        assert response.code == 200
        assert response_body["output"] == _gridfs_output()


class TestRequestListAPI:
    @pytest.mark.gen_test
    def test_post_file_parameter_stores_as_raw_file_on_local_garden(
        self,
        http_client,
        base_url,
        local_system,
    ):
        url = f"{base_url}/api/v1/requests"
        form_data = generate_form_data(local_system)
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
        base_url,
        remote_system,
        local_garden,
    ):
        url = f"{base_url}/api/v1/requests"
        form_data = generate_form_data(remote_system)
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

    @pytest.mark.gen_test
    def test_auth_disabled_returns_all_requests(self, http_client, base_url):
        url = f"{base_url}/api/v1/requests"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 2

    @pytest.mark.gen_test
    def test_auth_enabled_returns_permitted_requests(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        access_token,
        request_permitted,
    ):
        url = f"{base_url}/api/v1/requests"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 1
        assert response_body[0]["id"] == str(request_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_allows_post_permitted_request(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        user,
        access_token,
        request_permitted,
    ):
        url = f"{base_url}/api/v1/requests"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        request_before_count = len(Request.objects.all())

        post_body = {
            "system": request_permitted.system,
            "system_version": request_permitted.system_version,
            "namespace": request_permitted.namespace,
            "command": "mycommand",
            "instance_name": "default",
            "parameters": {"this": "doesntmatter"},
        }
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(post_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 201
        assert len(Request.objects.all()) == request_before_count + 1

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_post_for_not_permitted_request(
        self,
        http_client,
        base_url,
        app_config_auth_enabled,
        user,
        access_token,
        request_not_permitted,
    ):
        url = f"{base_url}/api/v1/requests"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        request_before_count = len(Request.objects.all())

        post_body = {
            "system": request_not_permitted.system,
            "system_version": request_not_permitted.system_version,
            "namespace": request_not_permitted.namespace,
            "command": "mycommand",
            "instance_name": "default",
            "parameters": {"this": "doesntmatter"},
        }
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(post_body)
        )
        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert len(Request.objects.all()) == request_before_count
