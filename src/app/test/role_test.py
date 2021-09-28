# -*- coding: utf-8 -*-
import pytest
from marshmallow import ValidationError
from mongoengine import DoesNotExist, connect

from beer_garden import config
from beer_garden.db.mongo.models import Role, RoleAssignment, User
from beer_garden.role import sync_roles


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
