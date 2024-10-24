# -*- coding: utf-8 -*-
import json

import pytest
from brewtils.models import Role, User
from brewtils.schema_parser import SchemaParser
from bson import ObjectId
from tornado.httpclient import HTTPError, HTTPRequest

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.api import MongoParser, from_brewtils
from beer_garden.db.mongo.models import Garden, Job, System
from beer_garden.role import create_role, delete_role
from beer_garden.user import create_user, delete_user


@pytest.fixture(autouse=True)
def garden(system_permitted, system_not_permitted):
    garden = Garden(
        name="permitted",
        connection_type="LOCAL",
        systems=[system_permitted, system_not_permitted],
    ).save()

    yield garden
    garden.delete()


@pytest.fixture
def system_permitted():
    system = System(name="permitted", version="1.0.0", namespace="permitted").save()

    yield system
    system.delete()


@pytest.fixture
def system_not_permitted():
    system = System(name="not_permitted", version="1.0.0", namespace="permitted").save()

    yield system
    system.delete()


@pytest.fixture
def job_manager_role(system_permitted):
    role = create_role(
        Role(
            name="job_manager",
            permission="OPERATOR",
            scope_systems=[system_permitted.name],
            scope_namespaces=[system_permitted.namespace],
        )
    )
    yield role
    delete_role(role)


@pytest.fixture
def user(job_manager_role):
    user = create_user(User(username="testuser", local_roles=[job_manager_role]))
    yield user
    delete_user(user=user)


@pytest.fixture
def access_token(user):
    yield issue_token_pair(user)["access"]


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


@pytest.fixture
def interval_job(bg_interval_job):
    bg_interval_job.id = None
    job = from_brewtils(bg_interval_job).save()

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
    def test_reset_interval(self, http_client, base_url, interval_job):
        url = f"{base_url}/api/v1/jobs/{interval_job.id}/execute?reset_interval=True"

        response = yield http_client.fetch(url, method="POST", body="")

        assert response.code == 202

    @pytest.mark.gen_test
    def test_reset_interval_on_non_interval_trigger_job(
        self,
        http_client,
        base_url,
        job_permitted,
    ):
        # job_permitted returns a job with a DateTrigger
        url = f"{base_url}/api/v1/jobs/{job_permitted.id}/execute?reset_interval=True"

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(url, method="POST", body="")

        assert excinfo.value.code == 400

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
        [ObjectId(), "111111111111111111111111"],
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
    @pytest.mark.gen_test
    def test_auth_disabled_allows_post(self, base_url, http_client, job_not_permitted):
        url = f"{base_url}/api/v1/import/jobs"

        import_job = MongoParser.serialize(job_not_permitted)
        import_job["id"] = None

        response = yield http_client.fetch(
            url, method="POST", body=json.dumps([import_job])
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
        url = f"{base_url}/api/v1/import/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}

        import_job = MongoParser.serialize(job_permitted)
        import_job["id"] = None

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=json.dumps([import_job])
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
        url = f"{base_url}/api/v1/import/jobs"
        headers = {"Authorization": f"Bearer {access_token}"}

        import_job = MongoParser.serialize(job_not_permitted)
        import_job["id"] = None

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(
                url, method="POST", headers=headers, body=json.dumps([import_job])
            )

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    def test_post_creates_only_valid_jobs(self, base_url, http_client, bg_job):
        url = f"{base_url}/api/v1/import/jobs"
        headers = {"Content-Type": "application/json"}

        valid_job = SchemaParser.serialize(bg_job)
        valid_job["id"] = None
        invalid_job = SchemaParser.serialize(bg_job)
        invalid_job["name"] = None

        post_body = json.dumps([valid_job, invalid_job])

        response = yield http_client.fetch(
            url, method="POST", headers=headers, body=post_body
        )
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 201
        assert len(response_body["ids"]) == 1
        assert len(Job.objects.all()) == 1
