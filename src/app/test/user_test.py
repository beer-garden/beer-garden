# -*- coding: utf-8 -*-
import pytest
from mongoengine import connect

from beer_garden.db.mongo.models import User
from beer_garden.user import create_user, update_user


class TestUser:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    @pytest.fixture(autouse=True)
    def drop_users(self):
        User.drop_collection()

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
