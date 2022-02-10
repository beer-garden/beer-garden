import json

import pytest

from beer_garden.db.mongo.models import Role


@pytest.fixture()
def roles():
    role1 = Role(name="role1").save()
    role2 = Role(name="role2").save()

    yield [role1, role2]
    role1.delete()
    role2.delete()


class TestRoleAPI:
    @pytest.mark.gen_test
    def test_get_returns_all_roles(self, http_client, base_url, roles):
        url = f"{base_url}/api/v1/roles/"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body["roles"]) == len(roles)
