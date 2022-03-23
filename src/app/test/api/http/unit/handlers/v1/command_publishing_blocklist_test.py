import json

import pytest
from tornado.httpclient import HTTPError, HTTPRequest

from beer_garden.api.http import CommandPublishingBlocklistListSchema
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.db.mongo.models import (
    CommandPublishingBlockList,
    Garden,
    Role,
    RoleAssignment,
    System,
    User,
)

garden_name = "somegarden"
system_name = "somesystem"
command_name = "somecommand"


@pytest.fixture
def blocklist():
    blocklist = CommandPublishingBlockList(
        namespace=garden_name, system=system_name, command=command_name
    )
    blocklist.save()

    yield blocklist
    blocklist.delete()


@pytest.fixture
def garden():
    garden = Garden(name=garden_name)
    garden.save()

    yield garden
    garden.delete()


@pytest.fixture
def system():
    system = System(name=system_name, namespace=garden_name, version="1.0.0dev0")
    system.save()

    yield system
    system.delete()


@pytest.fixture
def user_admin_role():
    role = Role(
        name="user_admin",
        permissions=["system:update", "system:read"],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def user_admin(user_admin_role):
    role_assignment = RoleAssignment(role=user_admin_role, domain={"scope": "Global"})
    user = User(username="useradmin")
    user.set_password("password")
    user.role_assignments = [role_assignment]
    user.save()

    yield user
    user.delete()


@pytest.fixture
def access_token_user_admin(user_admin):
    yield issue_token_pair(user_admin)["access"]


@pytest.fixture
def user_role():
    role = Role(
        name="user",
        permissions=[],
    ).save()

    yield role
    role.delete()


@pytest.fixture
def user(user_role):
    role_assignment = RoleAssignment(role=user_role, domain={"scope": "Global"})
    user = User(username="user")
    user.set_password("password")
    user.role_assignments = [role_assignment]
    user.save()

    yield user
    user.delete()


@pytest.fixture
def access_token_user(user):
    yield issue_token_pair(user)["access"]


@pytest.fixture
def blocklist_cleanup():
    yield
    CommandPublishingBlockList.drop_collection()


class TestCommandPublishingBlockListAPI:
    @pytest.mark.gen_test
    def test_delete(self, http_client, base_url, garden, blocklist):
        url = f"{base_url}/api/v1/commandpublishingblocklist/{blocklist.id}"
        request = HTTPRequest(url, method="DELETE")

        response = yield http_client.fetch(request)

        assert response.code == 204
        assert len(CommandPublishingBlockList.objects.filter(id=blocklist.id)) == 0

    @pytest.mark.gen_test
    def test_delete_404(self, http_client, base_url):
        url = f"{base_url}/api/v1/commandpublishingblocklist/624d8e8cce329715faf172d5"
        request = HTTPRequest(url, method="DELETE")

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 404

    @pytest.mark.gen_test
    def test_delete_auth(
        self,
        http_client,
        base_url,
        garden,
        blocklist,
        app_config_auth_enabled,
        access_token_user_admin,
    ):
        url = f"{base_url}/api/v1/commandpublishingblocklist/{blocklist.id}"
        headers = {
            "Authorization": f"Bearer {access_token_user_admin}",
            "Content-Type": "application/json",
        }
        request = HTTPRequest(url, headers=headers, method="DELETE")

        response = yield http_client.fetch(request)

        assert response.code == 204
        assert len(CommandPublishingBlockList.objects.filter(id=blocklist.id)) == 0

    @pytest.mark.gen_test
    def test_delete_auth_403_user_no_permisions(
        self,
        http_client,
        base_url,
        garden,
        blocklist,
        app_config_auth_enabled,
        access_token_user,
    ):
        url = f"{base_url}/api/v1/commandpublishingblocklist/{blocklist.id}"
        headers = {
            "Authorization": f"Bearer {access_token_user}",
            "Content-Type": "application/json",
        }
        request = HTTPRequest(url, headers=headers, method="DELETE")

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403

    @pytest.mark.gen_test
    def test_get(self, http_client, base_url, blocklist):
        url = f"{base_url}/api/v1/commandpublishingblocklist/"

        response = yield http_client.fetch(url)
        assert response.code == 200

        response_blocklist = json.loads(response.body.decode("utf-8"))
        blocklist_formated = (
            CommandPublishingBlocklistListSchema()
            .dump({"command_publishing_blocklist": [blocklist]})
            .data
        )
        assert response_blocklist == blocklist_formated

    @pytest.mark.gen_test
    def test_get_auth(
        self,
        http_client,
        base_url,
        blocklist,
        app_config_auth_enabled,
        access_token_user_admin,
    ):
        url = f"{base_url}/api/v1/commandpublishingblocklist/"
        headers = {"Authorization": f"Bearer {access_token_user_admin}"}
        request = HTTPRequest(url, headers=headers)

        response = yield http_client.fetch(request)
        assert response.code == 200

        response_blocklist = json.loads(response.body.decode("utf-8"))
        blocklist_formated = (
            CommandPublishingBlocklistListSchema()
            .dump({"command_publishing_blocklist": [blocklist]})
            .data
        )
        assert response_blocklist == blocklist_formated

    @pytest.mark.gen_test
    def test_get_auth_user_no_permissions(
        self,
        http_client,
        base_url,
        blocklist,
        app_config_auth_enabled,
        access_token_user,
    ):
        url = f"{base_url}/api/v1/commandpublishingblocklist/"
        headers = {
            "Authorization": f"Bearer {access_token_user}",
            "Content-Type": "application/json",
        }
        request = HTTPRequest(url, headers=headers)

        response = yield http_client.fetch(request)
        blocklist = json.loads(response.body.decode("utf-8"))
        assert response.code == 200
        assert len(blocklist["command_publishing_blocklist"]) == 0

    @pytest.mark.gen_test
    def test_post(self, http_client, base_url, garden, system, blocklist_cleanup):
        url = f"{base_url}/api/v1/commandpublishingblocklist/"

        headers = {"Content-Type": "application/json"}
        body = {
            "command_publishing_blocklist": [
                {
                    "namespace": garden.name,
                    "system": system.name,
                    "command": command_name,
                }
            ]
        }
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(body)
        )

        response = yield http_client.fetch(request)

        assert response.code == 201

    @pytest.mark.gen_test
    def test_post_400(self, http_client, base_url, garden, system):
        url = f"{base_url}/api/v1/commandpublishingblocklist/"

        headers = {"Content-Type": "application/json"}
        body = {
            "command_publishing_blocklist": [
                {"system": system.name, "command": command_name}
            ]
        }
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(body)
        )

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 400

    @pytest.mark.gen_test
    def test_post_auth(
        self,
        http_client,
        base_url,
        garden,
        system,
        app_config_auth_enabled,
        access_token_user_admin,
        blocklist_cleanup,
    ):
        url = f"{base_url}/api/v1/commandpublishingblocklist/"

        headers = {
            "Authorization": f"Bearer {access_token_user_admin}",
            "Content-Type": "application/json",
        }
        body = {
            "command_publishing_blocklist": [
                {
                    "namespace": garden.name,
                    "system": system.name,
                    "command": command_name,
                }
            ]
        }
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(body)
        )

        response = yield http_client.fetch(request)

        assert response.code == 201

    @pytest.mark.gen_test
    def test_post_auth_403_user_no_permissions(
        self,
        http_client,
        base_url,
        garden,
        system,
        app_config_auth_enabled,
        access_token_user,
    ):
        url = f"{base_url}/api/v1/commandpublishingblocklist/"

        headers = {
            "Authorization": f"Bearer {access_token_user}",
            "Content-Type": "application/json",
        }
        body = {
            "command_publishing_blocklist": [
                {
                    "namespace": garden.name,
                    "system": system.name,
                    "command": command_name,
                }
            ]
        }
        request = HTTPRequest(
            url, method="POST", headers=headers, body=json.dumps(body)
        )

        with pytest.raises(HTTPError) as excinfo:
            yield http_client.fetch(request)

        assert excinfo.value.code == 403
