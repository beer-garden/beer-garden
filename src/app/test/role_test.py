# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Event, Events
from marshmallow import ValidationError
from mock import Mock
from mongoengine import DoesNotExist, connect

import beer_garden.role
import beer_garden.router
from beer_garden import config
from beer_garden.db.mongo.models import Garden, RemoteRole, Role, RoleAssignment, User
from beer_garden.role import (
    RoleSyncSchema,
    handle_event,
    initiate_role_sync,
    role_sync,
    role_synced_with_garden,
    sync_roles,
)


@pytest.fixture(autouse=True)
def drop():
    Role.drop_collection()


@pytest.fixture
def role_sync_data():
    role_data = [
        {
            "name": "testrole1",
            "description": "a test role",
            "permissions": ["garden:read", "garden:create", "garden:update"],
        },
        {
            "name": "testrole2",
            "permissions": ["garden:read", "garden:delete"],
        },
    ]

    yield role_data


@pytest.fixture
def role_to_sync(role_sync_data):
    return Role(**role_sync_data[0])


@pytest.fixture
def remote_role(role_to_sync, gardens):
    remote_role = RemoteRole(
        name=role_to_sync.name,
        garden=gardens[0].name,
        description=role_to_sync.description,
        permissions=role_to_sync.permissions,
    )
    remote_role.save()

    yield remote_role
    remote_role.delete()


@pytest.fixture
def role_sync_data_missing_fields():
    role_data = [
        {
            "name": "badrole",
            "description": "hey",
        },
    ]

    yield role_data


@pytest.fixture
def user_with_role_assignments():
    role = Role(name="assignedrole1", permissions=["garden:read"]).save()
    role_assignment = RoleAssignment(
        domain={"scope": "Garden", "identifiers": {"name": "garden1"}}, role=role
    )
    user = User(username="testuser", role_assignments=[role_assignment]).save()

    yield user
    user.delete()
    role.delete()


@pytest.fixture
def gardens():
    garden1 = Garden(name="garden1", connection_type="HTTP", status="RUNNING").save()
    garden2 = Garden(name="garden2", connection_type="HTTP", status="RUNNING").save()
    garden3 = Garden(name="garden2", connection_type="HTTP", status="STOPPED").save()

    yield [garden1, garden2, garden3]
    garden1.delete()
    garden2.delete()
    garden3.delete()


class TestRole:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")
        config._CONFIG = {"garden": {"name": "localgarden"}}

    def test_sync_roles_creates_new_roles(self, role_sync_data):
        """sync_roles should create new roles when none exists"""
        role_names = [role["name"] for role in role_sync_data]

        sync_roles(role_sync_data)

        assert len(Role.objects.filter(name__in=role_names)) == len(role_sync_data)

    def test_sync_roles_deletes_roles_not_present(self, role_sync_data):
        """sync_roles should delete roles in the database that are are not present in
        the role_sync_data
        """
        Role(name="notinsyncdata", permissions=["garden:read"]).save()

        sync_roles(role_sync_data)

        with pytest.raises(DoesNotExist):
            Role.objects.get(name="notinsyncdata")

    def test_sync_roles_updates_existing_roles(self, role_sync_data):
        """sync_roles should update any existing Roles based on what is in the provided
        role_sync_data
        """
        Role(
            name="testrole1", description="somethingwitty", permissions=["system:read"]
        ).save()

        sync_roles(role_sync_data)

        role = Role.objects.get(name="testrole1")

        assert role.description == role_sync_data[0]["description"]
        assert role.permissions == role_sync_data[0]["permissions"]

    def test_sync_roles_raises_validation_error_for_missing_fields(
        self, role_sync_data_missing_fields
    ):
        """sync_roles should raise a ValidationError if any required fields are missing
        in the supply input sync data
        """
        with pytest.raises(ValidationError):
            sync_roles(role_sync_data_missing_fields)

    def test_sync_roles_removes_user_role_assignments(
        self, role_sync_data, user_with_role_assignments
    ):
        """sync_roles should remove role assignments references Roles that are deleted
        as part of the sync process
        """
        assert len(user_with_role_assignments.role_assignments) > 0

        sync_roles(role_sync_data)
        user_with_role_assignments.reload()

        assert len(user_with_role_assignments.role_assignments) == 0

    def test_initiate_role_sync_routes_to_each_running_garden(
        self, monkeypatch, gardens
    ):
        monkeypatch.setattr(beer_garden.router, "route", Mock())
        Role(name="testrole").save()
        initiate_role_sync()

        assert beer_garden.router.route.call_count == len(
            Garden.objects.filter(status="RUNNING")
        )

    def test_role_sync_creates_role(self, monkeypatch, role_to_sync):
        monkeypatch.setattr(beer_garden.role, "initiate_role_sync", Mock())
        monkeypatch.setattr(beer_garden.role, "publish", Mock())
        serialized_role = RoleSyncSchema().dump(role_to_sync).data

        assert len(Role.objects.filter(name=role_to_sync.name)) == 0

        role_sync([serialized_role])

        assert len(Role.objects.filter(name=role_to_sync.name)) == 1
        assert beer_garden.role.publish.called is True

    def test_role_sync_updates_role(self, monkeypatch, role_to_sync):
        monkeypatch.setattr(beer_garden.role, "initiate_role_sync", Mock())
        monkeypatch.setattr(beer_garden.role, "publish", Mock())
        serialized_role = RoleSyncSchema().dump(role_to_sync).data
        expected_permissions = role_to_sync.permissions
        role_to_sync.permissions = []
        role_to_sync.save()

        role_sync([serialized_role])
        role_to_sync.reload()

        assert set(role_to_sync.permissions) == set(expected_permissions)

    def test_role_synced_with_garden_returns_false_for_no_remote_role(
        self, role_to_sync, gardens
    ):
        assert role_synced_with_garden(role_to_sync, gardens[0]) is False

    def test_role_synced_with_garden_returns_false_for_non_matching_permissions(
        self, role_to_sync, remote_role
    ):
        garden = Garden.objects.get(name=remote_role.garden)
        role_to_sync.permissions = []

        assert role_synced_with_garden(role_to_sync, garden) is False

    def test_role_synced_with_garden_returns_true_for_matching_permissions(
        self, role_to_sync, remote_role
    ):
        garden = Garden.objects.get(name=remote_role.garden)

        assert role_synced_with_garden(role_to_sync, garden) is True

    def test_handle_event_for_role_updated(self):
        permissions = ["queue:read", "queue:delete"]
        role_updated_result = {
            "garden": "garden1",
            "role": {"name": "role1", "permissions": permissions},
        }

        event = Event(
            name=Events.ROLE_UPDATED.name,
            garden="garden1",
            metadata=role_updated_result,
        )

        assert len(RemoteRole.objects.filter(name="role1", garden="garden1")) == 0

        handle_event(event)
        remote_role = RemoteRole.objects.get(name="role1", garden="garden1")

        assert remote_role.permissions == permissions
