# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Event, Events
from marshmallow import ValidationError
from mock import Mock
from mongoengine import DoesNotExist, connect

from beer_garden import config
from beer_garden.db.mongo.models import Garden, RemoteRole, Role, RoleAssignment, User
from beer_garden.role import handle_event, role_sync_status, sync_roles


@pytest.fixture(autouse=True)
def drop():
    Role.drop_collection()


@pytest.fixture
def garden():
    _garden = Garden(name="garden", connection_type="HTTP", status="RUNNING").save()

    yield _garden
    _garden.delete()


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
def remote_role(role_to_sync, garden):
    remote_role = RemoteRole(
        name=role_to_sync.name,
        garden=garden.name,
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
def role_sync_data_protected_role():
    role_data = [
        {
            "name": "protected_role",
            "description": "can't touch this",
            "permissions": ["garden:read"],
            "protected": True,
        }
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

    def test_role_synced_with_garden_returns_false_for_no_remote_role(
        self, role_to_sync, garden
    ):
        role_status = role_sync_status([role_to_sync])[role_to_sync.name]

        assert role_status[garden.name] is False

    def test_role_synced_with_garden_returns_false_for_non_matching_permissions(
        self, role_to_sync, remote_role
    ):
        garden = Garden.objects.get(name=remote_role.garden)
        role_to_sync.permissions = []

        role_status = role_sync_status([role_to_sync])[role_to_sync.name]

        assert role_status[garden.name] is False

    def test_role_synced_with_garden_returns_true_for_matching_permissions(
        self, role_to_sync, remote_role
    ):
        role_status = role_sync_status([role_to_sync])[role_to_sync.name]
        garden = Garden.objects.get(name=remote_role.garden)

        assert role_status[garden.name] is True

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

    def test_sync_roles_skips_protected_roles(
        self, monkeypatch, role_sync_data_protected_role
    ):
        Role(**role_sync_data_protected_role[0]).save()
        monkeypatch.setattr(Role, "save", Mock())

        sync_roles(role_sync_data_protected_role)

        assert Role.save.called is False

    def test_sync_roles_preserves_unlisted_protected_roles(
        self, role_sync_data_protected_role, role_sync_data
    ):
        protected_role = Role(**role_sync_data_protected_role[0]).save()

        # role_sync_data does not include the protected role
        sync_roles(role_sync_data)

        assert Role.objects.get(name=protected_role.name).id == protected_role.id
