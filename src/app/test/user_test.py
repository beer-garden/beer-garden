# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Event, Events
from mock import Mock
from mongoengine import connect

import beer_garden.events
import beer_garden.router
import beer_garden.user
from beer_garden.api.http.schemas.v1.user import UserSyncSchema
from beer_garden.db.mongo.models import (
    Garden,
    RemoteRole,
    RemoteUser,
    Role,
    RoleAssignment,
    User,
)
from beer_garden.role import RoleSyncSchema
from beer_garden.user import (
    create_user,
    handle_event,
    initiate_user_sync,
    update_user,
    user_sync,
    user_sync_status,
)


class TestUser:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.fixture(autouse=True)
    def drop_users(self):
        yield
        User.drop_collection()

    @pytest.fixture
    def garden(self):
        _garden = Garden(name="garden", connection_type="HTTP", status="RUNNING").save()

        yield _garden
        _garden.delete()

    @pytest.fixture
    def garden_with_role(self, user_role):
        garden = Garden(
            name="garden_with_role", connection_type="HTTP", status="RUNNING"
        ).save()
        remote_role = RemoteRole(name=user_role.name, garden=garden.name).save()

        yield garden
        garden.delete()
        remote_role.delete()

    @pytest.fixture
    def garden_stopped(self):
        garden = Garden(
            name="garden_stopped", connection_type="HTTP", status="STOPPED"
        ).save()

        yield garden
        garden.delete()

    @pytest.fixture
    def gardens(self, garden, garden_with_role, garden_stopped):
        return [garden, garden_with_role, garden_stopped]

    @pytest.fixture
    def user_role(self):
        role = Role(name="role1").save()

        yield role
        role.delete()

    @pytest.fixture
    def user_to_sync(self, user_role):
        role_assignment = RoleAssignment(role=user_role, domain={"scope": "Global"})
        user = User(
            username="testuser", password="password", role_assignments=[role_assignment]
        )

        return user

    @pytest.fixture
    def serialized_role(self, user_role):
        return RoleSyncSchema().dump(user_role).data

    @pytest.fixture
    def remote_user(self, user_to_sync, garden_with_role):
        remote_user = RemoteUser(
            username=user_to_sync.username, garden=garden_with_role.name
        )
        remote_user.role_assignments = (
            UserSyncSchema().dump(user_to_sync).data["role_assignments"]
        )
        remote_user.save()

        yield remote_user
        remote_user.delete()

    def test_create_user(self):
        user = create_user(username="testuser", password="password")

        assert type(user) is User
        assert user.username == "testuser"
        assert user.password != "password"
        assert User.objects.filter(username="testuser").count() == 1

    def test_update_user(self):
        user = User(username="testuser", password="password")
        user.save()

        prev_password = user.password

        updated_user = update_user(
            user, username="differentuser", password="badpassword"
        )

        assert type(updated_user) is User
        assert User.objects.filter(username="testuser").count() == 0
        assert User.objects.filter(username="differentuser").count() == 1
        assert updated_user.username == "differentuser"

        # Check for differences rather than actual values to avoid making these
        # assertions dependent on our specific hashing algorithm. We check that:
        # 1) The password changed
        # 2) It is not the plaintext password we provided
        assert updated_user.password != prev_password
        assert updated_user.password != "badpassword"

    def test_initiate_user_sync_routes_to_each_running_garden(
        self, monkeypatch, gardens
    ):
        monkeypatch.setattr(beer_garden.router, "route", Mock())
        User(username="testuser").save()
        initiate_user_sync()

        assert beer_garden.router.route.call_count == len(
            Garden.objects.filter(status="RUNNING")
        )

    def test_user_sync_creates_user(self, monkeypatch, user_to_sync, serialized_role):
        monkeypatch.setattr(beer_garden.user, "initiate_user_sync", Mock())
        monkeypatch.setattr(beer_garden.user, "publish", Mock())
        serialized_user = UserSyncSchema().dump(user_to_sync).data

        assert len(User.objects.filter(username=user_to_sync.username)) == 0

        user_sync([serialized_role], [serialized_user])

        assert len(User.objects.filter(username=user_to_sync.username)) == 1
        assert beer_garden.user.publish.called is True

    def test_user_sync_updates_user(self, monkeypatch, user_to_sync, serialized_role):
        monkeypatch.setattr(beer_garden.user, "initiate_user_sync", Mock())
        monkeypatch.setattr(beer_garden.user, "publish", Mock())
        serialized_user = UserSyncSchema().dump(user_to_sync).data
        user_to_sync.role_assignments = []
        user_to_sync.save()

        user_sync([serialized_role], [serialized_user])
        user_to_sync.reload()
        assert len(user_to_sync.role_assignments) == 1

    def test_user_sync_status_returns_false_for_no_remote_user(
        self, user_to_sync, garden
    ):
        user_status = user_sync_status([user_to_sync])[user_to_sync.username]

        assert user_status[garden.name] is False

    def test_user_sync_status_returns_false_for_non_matching_role_assignments(
        self, user_to_sync, remote_user
    ):
        garden = Garden.objects.get(name=remote_user.garden)
        user_to_sync.role_assignments = []
        user_status = user_sync_status([user_to_sync])[user_to_sync.username]

        assert user_status[garden.name] is False

    def test_user_sync_status_returns_true_for_matching_role_assignments(
        self, user_to_sync, remote_user
    ):
        garden = Garden.objects.get(name=remote_user.garden)
        user_status = user_sync_status([user_to_sync])[user_to_sync.username]

        assert user_status[garden.name] is True

    def test_user_sync_status_returns_true_for_no_relevant_assignments(self, garden):
        user = User(username="user")

        user_status = user_sync_status([user])[user.username]
        assert user_status[garden.name] is True

    def test_user_sync_status_returns_false_for_out_of_sync_roles(
        self, user_to_sync, remote_user, garden_with_role
    ):
        remote_role = RemoteRole.objects.get(garden=garden_with_role.name)
        remote_role.description = "No longer in sync"
        remote_role.save()

        user_status = user_sync_status([user_to_sync])[user_to_sync.username]

        assert user_status[garden_with_role.name] is False

    def test_handle_event_for_user_updated(self):
        role_assignments = [{"role_name": "role1", "domain": {"scope": "Global"}}]
        user_updated_result = {
            "garden": "garden1",
            "user": {"username": "user1", "role_assignments": role_assignments},
        }

        event = Event(
            name=Events.USER_UPDATED.name,
            garden="garden1",
            metadata=user_updated_result,
        )

        assert len(RemoteUser.objects.filter(username="user1", garden="garden1")) == 0

        handle_event(event)
        remote_user = RemoteUser.objects.get(username="user1", garden="garden1")

        assert remote_user.role_assignments == role_assignments
