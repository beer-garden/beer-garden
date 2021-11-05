# -*- coding: utf-8 -*-
import json
from unittest.mock import Mock

import pytest
from bson import ObjectId
from tornado.httpclient import HTTPError, HTTPRequest

import beer_garden.router
from beer_garden.api.http.authentication import generate_access_token
from beer_garden.db.mongo.api import MongoParser, from_brewtils
from beer_garden.db.mongo.models import Garden, Job, Role, RoleAssignment, System, User


@pytest.fixture
def garden():
    garden = Garden(name="permitted", connection_type="LOCAL").save()

    yield garden
    garden.delete()


@pytest.fixture
def system_permitted(garden):
    system = System(name="permitted", version="1.0.0", namespace=garden.name).save()

    yield system
    system.delete()


@pytest.fixture
def system_not_permitted(garden):
    system = System(name="not_permitted", version="1.0.0", namespace=garden.name).save()

    yield system
    system.delete()


@pytest.fixture
def job_manager_role():
    role = Role(
        name="job_manager",
        permissions=[
            "job:create",
            "job:read",
            "job:update",
            "job:delete",
        ],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def user(system_permitted, job_manager_role):
    role_assignment = RoleAssignment(
        role=job_manager_role,
        domain={
            "scope": "System",
            "identifiers": {
                "name": system_permitted.name,
                "namespace": system_permitted.namespace,
            },
        },
    )

    user = User(username="testuser", role_assignments=[role_assignment]).save()

    yield user
    user.delete()


@pytest.fixture
def access_token(user):
    yield generate_access_token(user)


@pytest.fixture
def job_permitted(bg_job, system_permitted):
    bg_job.id = None
    bg_job.request_template.namespace = system_permitted.namespace
    bg_job.request_template.system = system_permitted.name
    job = from_brewtils(bg_job).save()

    yield job
    job.delete()


@pytest.fixture
def job_not_permitted(bg_job, system_not_permitted):
    bg_job.id = None
    bg_job.request_template.namespace = system_not_permitted.namespace
    bg_job.request_template.system = system_not_permitted.name
    job = from_brewtils(bg_job).save()

    yield job
    job.delete()


@pytest.fixture(autouse=True)
def drop_jobs():
    yield
    Job.drop_collection()


class TestJobAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_get(self, base_url, http_client, job_not_permitted):
        url = f"{base_url}/api/v1/jobs/{job_not_permitted.id}"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == str(job_not_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_allows_get_for_permitted_job(
        self,
        base_url,
        http_client,
        app_config_auth_enabled,
        job_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs/{job_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert response_body["id"] == str(job_permitted.id)

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_get_for_not_permitted_job(
        self,
        base_url,
        http_client,
        app_config_auth_enabled,
        job_not_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs/{job_not_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, headers=headers)

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    def test_auth_disabled_allows_patch(self, base_url, http_client, job_not_permitted):
        url = f"{base_url}/api/v1/jobs/{job_not_permitted.id}"
        patch_body = {"operation": "update", "path": "/status", "value": "PAUSED"}
        headers = {"Content-Type": "application/json"}

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 200
        assert Job.objects.get(id=job_not_permitted.id).status == "PAUSED"

    @pytest.mark.gen_test
    def test_auth_enabled_allows_patch_for_permitted_job(
        self,
        base_url,
        http_client,
        app_config_auth_enabled,
        job_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs/{job_permitted.id}"
        patch_body = {"operation": "update", "path": "/status", "value": "PAUSED"}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        response = yield http_client.fetch(request)

        assert response.code == 200
        assert Job.objects.get(id=job_permitted.id).status == "PAUSED"

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_patch_for_not_permitted_job(
        self,
        base_url,
        http_client,
        app_config_auth_enabled,
        job_not_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs/{job_not_permitted.id}"
        patch_body = {"operation": "update", "path": "/status", "value": "PAUSED"}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=json.dumps(patch_body)
        )
        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert Job.objects.get(id=job_not_permitted.id).status == "RUNNING"

    @pytest.mark.gen_test
    def test_auth_disabled_allows_delete(
        self, base_url, http_client, job_not_permitted
    ):
        url = f"{base_url}/api/v1/jobs/{job_not_permitted.id}"

        request = HTTPRequest(url, method="DELETE")
        response = yield http_client.fetch(request)

        assert response.code == 204

    @pytest.mark.gen_test
    def test_auth_enabled_allows_delete_for_permitted_job(
        self,
        base_url,
        http_client,
        app_config_auth_enabled,
        job_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs/{job_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)
        response = yield http_client.fetch(request)

        assert response.code == 204

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_delete_for_not_permitted_job(
        self,
        base_url,
        http_client,
        app_config_auth_enabled,
        job_not_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs/{job_not_permitted.id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        request = HTTPRequest(url, method="DELETE", headers=headers)
        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
        assert len(Job.objects.filter(id=job_not_permitted.id)) == 1


class TestJobListAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_get(
        self, base_url, http_client, job_permitted, job_not_permitted
    ):
        url = f"{base_url}/api/v1/jobs"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 2

    @pytest.mark.gen_test
    def test_auth_enabled_returns_permitted_jobs(
        self,
        base_url,
        http_client,
        app_config_auth_enabled,
        job_permitted,
        job_not_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, headers=headers)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 1
        assert response_body[0]["id"] == str(job_permitted.id)

    @pytest.mark.gen_test
    def test_auth_disabled_allows_post(
        self,
        base_url,
        http_client,
        job_not_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}

        new_job = MongoParser.serialize(job_not_permitted)
        new_job["id"] = None

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=json.dumps(new_job)
        )

        assert response.code == 201

    @pytest.mark.gen_test
    def test_auth_enabled_allows_post_for_permitted_job(
        self,
        base_url,
        http_client,
        job_permitted,
        app_config_auth_enabled,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}

        new_job = MongoParser.serialize(job_permitted)
        new_job["id"] = None

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=json.dumps(new_job)
        )

        assert response.code == 201

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_post_for_not_permitted_job(
        self,
        base_url,
        http_client,
        job_not_permitted,
        app_config_auth_enabled,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}

        new_job = MongoParser.serialize(job_not_permitted)
        new_job["id"] = None

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(
                url, method="POST", headers=headers, body=json.dumps(new_job)
            )

        assert excinfo.value.code == 403


class TestJobExecutionAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_post(self, base_url, http_client, job_not_permitted):
        url = f"{base_url}/api/v1/jobs/{job_not_permitted.id}/execute"

        response = yield http_client.fetch(url, method="POST", body="")

        assert response.code == 202

    @pytest.mark.gen_test
    def test_auth_enabled_allows_post_for_permitted_job(
        self,
        base_url,
        http_client,
        app_config_auth_enabled,
        job_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs/{job_permitted.id}/execute"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(url, method="POST", headers=headers, body="")

        assert response.code == 202

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_post_for_not_permitted_job(
        self,
        base_url,
        http_client,
        app_config_auth_enabled,
        job_not_permitted,
        access_token,
    ):
        url = f"{base_url}/api/v1/jobs/{job_not_permitted.id}/execute"
        headers = {"Authorization": f"Bearer {access_token}"}

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", headers=headers, body="")

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    @pytest.mark.parametrize(
        "job_id",
        [
            ObjectId(),
            "not_real",
        ],
    )
    def test_execute_job_not_found(self, http_client, base_url, job_id):
        url = f"{base_url}/api/v1/jobs/{job_id}/execute"

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body="")

        assert excinfo.value.code == 404


class TestJobExportAPI:
    @pytest.mark.gen_test
    def test_auth_disabled_allows_export(
        self, base_url, http_client, job_permitted, job_not_permitted
    ):
        url = f"{base_url}/api/v1/export/jobs"

        response = yield http_client.fetch(url, method="POST", body="{}")
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 2

    @pytest.mark.gen_test
    def test_auth_enabled_allows_export_of_permitted_jobs(
        self,
        base_url,
        http_client,
        job_permitted,
        job_not_permitted,
        app_config_auth_enabled,
        access_token,
    ):
        url = f"{base_url}/api/v1/export/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body="{}"
        )
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 1
        assert (
            response_body[0]["request_template"]["system"]
            == job_permitted.request_template.system
        )

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_export_of_not_permitted_jobs(
        self,
        base_url,
        http_client,
        job_permitted,
        job_not_permitted,
        app_config_auth_enabled,
        access_token,
    ):
        url = f"{base_url}/api/v1/export/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}
        body = {"ids": [str(job_not_permitted.id)]}

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=json.dumps(body)
        )
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == 0


class TestJobImportAPI:
    @pytest.fixture
    def import_function_mock(self):
        import_function = Mock()
        import_function.return_value = {}

        return import_function

    @pytest.fixture(autouse=True)
    def common_mocks(self, monkeypatch, import_function_mock):
        route_functions = {
            "JOB_CREATE_MULTI": import_function_mock,
        }

        monkeypatch.setattr(beer_garden.router, "route_functions", route_functions)

    @pytest.mark.gen_test
    def test_auth_disabled_allows_post(
        self, import_function_mock, base_url, http_client, job_not_permitted
    ):
        url = f"{base_url}/api/v1/import/jobs"

        import_job = MongoParser.serialize(job_not_permitted)
        import_job["id"] = None

        response = yield http_client.fetch(
            url, method="POST", body=json.dumps([import_job])
        )

        assert response.code == 201
        assert import_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_allows_post_for_permitted_job(
        self,
        import_function_mock,
        base_url,
        http_client,
        job_permitted,
        app_config_auth_enabled,
        access_token,
    ):
        url = f"{base_url}/api/v1/import/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}

        import_job = MongoParser.serialize(job_permitted)
        import_job["id"] = None

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=json.dumps([import_job])
        )

        assert response.code == 201
        assert import_function_mock.called is True

    @pytest.mark.gen_test
    def test_auth_enabled_rejects_post_for_not_permitted_job(
        self,
        import_function_mock,
        base_url,
        http_client,
        job_not_permitted,
        app_config_auth_enabled,
        access_token,
    ):
        url = f"{base_url}/api/v1/import/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}

        import_job = MongoParser.serialize(job_not_permitted)
        import_job["id"] = None

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(
                url, method="POST", headers=headers, body=json.dumps([import_job])
            )

        assert excinfo.value.code == 403
        assert import_function_mock.called is False
