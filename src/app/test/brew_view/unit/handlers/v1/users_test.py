# -*- coding: utf-8 -*-
import json

import pytest
from tornado.httpclient import HTTPRequest

from bg_utils.mongo.models import Principal, Role
from brewtils.models import PatchOperation
from brewtils.schema_parser import SchemaParser


@pytest.fixture(autouse=True)
def drop_principals(app):
    Principal.drop_collection()
    Role.drop_collection()


class TestPrincipalAPI(object):
    @pytest.mark.gen_test
    def test_get(self, http_client, base_url, mongo_principal, mongo_role):
        mongo_role.save()
        mongo_principal.save()
        url = base_url + "/api/v1/users/" + str(mongo_principal.id)
        response = yield http_client.fetch(url)
        assert 200 == response.code
        response_principal = json.loads(response.body.decode("utf-8"))
        assert response_principal["id"] == str(mongo_principal.id)

    @pytest.mark.gen_test
    @pytest.mark.parametrize(
        "operation,value,expected_username,succeed",
        [
            ("update", "new_username", "new_username", True),
            ("INVALID", None, None, False),
        ],
    )
    def test_patch_users_username(
        self,
        http_client,
        base_url,
        mongo_principal,
        mongo_role,
        operation,
        value,
        expected_username,
        succeed,
    ):
        mongo_role.save()
        mongo_principal.save()

        body = PatchOperation(operation=operation, path="/username", value=value)

        request = HTTPRequest(
            base_url + "/api/v1/users/" + str(mongo_principal.id),
            method="PATCH",
            headers={"content-type": "application/json"},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        if succeed:
            assert response.code == 200
            updated = SchemaParser.parse_principal(
                response.body.decode("utf-8"), from_string=True
            )
            assert updated.username == expected_username

        else:
            assert response.code >= 400

    @pytest.mark.gen_test
    def test_patch_add_role(self, http_client, base_url, mongo_principal, mongo_role):
        mongo_role.save()
        mongo_principal.save()
        new_role = Role(
            name="new_role", description="Some desc", roles=[], permissions=["bg-all"]
        )
        new_role.save()

        body = PatchOperation(operation="add", path="/roles", value="new_role")

        url = base_url + "/api/v1/users/" + str(mongo_principal.id)
        request = HTTPRequest(
            url,
            method="PATCH",
            headers={"content-type": "application/json"},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        assert response.code == 200
        updated = SchemaParser.parse_principal(
            response.body.decode("utf-8"), from_string=True
        )
        assert len(updated.roles) == 2

    @pytest.mark.gen_test
    def test_patch_remove_role(
        self, http_client, base_url, mongo_principal, mongo_role
    ):
        mongo_role.save()
        mongo_principal.save()
        body = PatchOperation(operation="remove", path="/roles", value=mongo_role.name)

        url = base_url + "/api/v1/users/" + str(mongo_principal.id)
        request = HTTPRequest(
            url,
            method="PATCH",
            headers={"content-type": "application/json"},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        assert response.code == 200
        updated = SchemaParser.parse_principal(
            response.body.decode("utf-8"), from_string=True
        )
        assert len(updated.roles) == 0

    @pytest.mark.gen_test
    def test_patch_set_roles(self, http_client, base_url, mongo_principal, mongo_role):
        mongo_role.save()
        mongo_principal.save()
        new_role = Role(
            name="new_role", description="Some desc", roles=[], permissions=["bg-all"]
        )
        new_role.save()

        body = PatchOperation(operation="set", path="/roles", value=["new_role"])

        url = base_url + "/api/v1/users/" + str(mongo_principal.id)
        request = HTTPRequest(
            url,
            method="PATCH",
            headers={"content-type": "application/json"},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        assert response.code == 200
        updated = SchemaParser.parse_principal(
            response.body.decode("utf-8"), from_string=True
        )
        assert len(updated.roles) == 1
        assert updated.roles[0].name == "new_role"

    @pytest.mark.gen_test
    def test_patch_invalid_role(
        self, http_client, base_url, mongo_principal, mongo_role
    ):
        mongo_role.save()
        mongo_principal.save()

        body = PatchOperation(operation="add", path="/roles", value=["DOES_NOT_EXIST"])

        url = base_url + "/api/v1/users/" + str(mongo_principal.id)
        request = HTTPRequest(
            url,
            method="PATCH",
            headers={"content-type": "application/json"},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        assert response.code == 400

    @pytest.mark.gen_test
    def test_patch_invalid_password_op(
        self, http_client, base_url, mongo_principal, mongo_role
    ):
        mongo_role.save()
        mongo_principal.save()

        body = PatchOperation(
            operation="INVALID", path="/password", value="new_password"
        )

        url = base_url + "/api/v1/users/" + str(mongo_principal.id)
        request = HTTPRequest(
            url,
            method="PATCH",
            headers={"content-type": "application/json"},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        assert response.code == 400

    @pytest.mark.gen_test
    def test_patch_password_update(
        self, http_client, base_url, mongo_principal, mongo_role
    ):
        mongo_role.save()
        mongo_principal.save()

        body = PatchOperation(
            operation="update", path="/password", value="new_password"
        )
        url = base_url + "/api/v1/users/" + str(mongo_principal.id)
        request = HTTPRequest(
            url,
            method="PATCH",
            headers={"content-type": "application/json"},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        assert response.code == 200

    @pytest.mark.gen_test
    def test_patch_password_update_meta(
        self, http_client, base_url, mongo_principal, mongo_role
    ):
        mongo_role.save()
        mongo_principal.metadata = {"auto_change": True, "changed": False}
        mongo_principal.save()
        body = PatchOperation(
            operation="update", path="/password", value="new_password"
        )

        url = base_url + "/api/v1/users/" + str(mongo_principal.id)
        request = HTTPRequest(
            url,
            method="PATCH",
            headers={"content-type": "application/json"},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        assert response.code == 200
        updated = SchemaParser.parse_principal(
            response.body.decode("utf-8"), from_string=True
        )
        assert updated.metadata.get("changed") is True
