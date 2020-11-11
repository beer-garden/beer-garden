# -*- coding: utf-8 -*-
import pytest
from tornado.httpclient import HTTPRequest

from beer_garden.db.mongo.models import Role
from brewtils.models import PatchOperation
from brewtils.schema_parser import SchemaParser


@pytest.fixture(autouse=True)
def drop_roles(app):
    Role.drop_collection()


@pytest.mark.skip("TODO")
class TestRolesAPI(object):
    @pytest.mark.gen_test
    @pytest.mark.parametrize(
        "operation,value,expected_value,succeed",
        [
            ("update", "new_description", "new_description", True),
            ("INVALID", None, None, False),
        ],
    )
    def test_patch_role_description(
        self,
        http_client,
        base_url,
        mongo_role,
        operation,
        value,
        expected_value,
        succeed,
    ):
        mongo_role.save()

        body = PatchOperation(operation=operation, path="/description", value=value)

        request = HTTPRequest(
            base_url + "/api/v1/roles/" + str(mongo_role.id),
            method="PATCH",
            headers={"content-type": "application/json"},
            body=SchemaParser.serialize_patch(body),
        )
        response = yield http_client.fetch(request, raise_error=False)

        if succeed:
            assert response.code == 200
            updated = SchemaParser.parse_role(
                response.body.decode("utf-8"), from_string=True
            )
            assert updated.description == expected_value

        else:
            assert response.code >= 400
