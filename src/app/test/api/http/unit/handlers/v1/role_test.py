import json

import pytest
from brewtils.models import Role

from beer_garden.db.mongo.models import Garden
from beer_garden.role import create_role, delete_role


@pytest.fixture()
def roles():
    role1 = create_role(Role(name="role1", permission="OPERATOR"))
    role2 = create_role(Role(name="role2", permission="OPERATOR"))
    yield [role1, role2]
    delete_role(role1)
    delete_role(role2)


@pytest.fixture(autouse=True)
def local_garden():
    garden = Garden(name="somegarden", connection_type="LOCAL").save()

    yield garden
    garden.delete()


class TestRoleAPI:
    @pytest.mark.gen_test
    def test_get_returns_all_roles(self, http_client, base_url, roles):
        url = f"{base_url}/api/v1/roles/"

        response = yield http_client.fetch(url)
        response_body = json.loads(response.body.decode("utf-8"))

        assert response.code == 200
        assert len(response_body) == len(roles)
