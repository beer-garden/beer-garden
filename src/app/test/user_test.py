# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Event, Events
from mock import Mock
from mongoengine import connect

import beer_garden.events
import beer_garden.router
import beer_garden.user
from beer_garden.api.http.schemas.v1.user import UserSyncSchema
from beer_garden.db.mongo.models import Garden, RemoteUser, Role, RoleAssignment, User
from beer_garden.user import (
    create_user,
    handle_event,
    initiate_user_sync,
    update_user,
    user_sync,
    user_synced_with_garden,
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
    def gardens(self):
        garden1 = Garden(
            name="garden1", connection_type="HTTP", status="RUNNING"
        ).save()
        garden2 = Garden(
            name="garden2", connection_type="HTTP", status="RUNNING"
        ).save()
        garden3 = Garden(
            name="garden2", connection_type="HTTP", status="STOPPED"
        ).save()

        yield [garden1, garden2, garden3]
        garden1.delete()
        garden2.delete()
        garden3.delete()

    @pytest.fixture
    def user_to_sync(self):
        role = Role(name="role1").save()
        role_assignment = RoleAssignment(role=role, domain={"scope": "Global"})
        user = User(
            username="testuser", password="password", role_assignments=[role_assignment]
        )

        yield user
        role.delete()

    @pytest.fixture
    def remote_user(self, user_to_sync, gardens):
        remote_user = RemoteUser(username=user_to_sync.username, garden=gardens[0].name)
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

    def test_user_sync_creates_user(self, monkeypatch, user_to_sync):
        monkeypatch.setattr(beer_garden.user, "initiate_user_sync", Mock())
        monkeypatch.setattr(beer_garden.user, "publish", Mock())
        serialized_user = UserSyncSchema().dump(user_to_sync).data

        assert len(User.objects.filter(username=user_to_sync.username)) == 0

        user_sync([serialized_user])

        assert len(User.objects.filter(username=user_to_sync.username)) == 1
        assert beer_garden.user.publish.called is True

    def test_user_sync_updates_user(self, monkeypatch, user_to_sync):
        monkeypatch.setattr(beer_garden.user, "initiate_user_sync", Mock())
        monkeypatch.setattr(beer_garden.user, "publish", Mock())
        serialized_user = UserSyncSchema().dump(user_to_sync).data
        user_to_sync.role_assignments = []
        user_to_sync.save()

        user_sync([serialized_user])
        user_to_sync.reload()
        assert len(user_to_sync.role_assignments) == 1

    def test_user_synced_with_garden_returns_false_for_no_remote_user(
        self, user_to_sync, gardens
    ):
        assert user_synced_with_garden(user_to_sync, gardens[0]) is False

    def test_user_synced_with_garden_returns_false_for_non_matching_role_assignments(
        self, user_to_sync, remote_user
    ):
        garden = Garden.objects.get(name=remote_user.garden)
        user_to_sync.role_assignments = []

        assert user_synced_with_garden(user_to_sync, garden) is False

    def test_user_synced_with_garden_returns_true_for_matching_role_assignments(
        self, user_to_sync, remote_user
    ):
        garden = Garden.objects.get(name=remote_user.garden)

        assert user_synced_with_garden(user_to_sync, garden) is True

    def test_user_synced_with_garden_returns_true_for_no_relevant_assignments(self):
        user = User(username="user")
        garden = Garden(name="garden")

        assert user_synced_with_garden(user, garden) is True

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
