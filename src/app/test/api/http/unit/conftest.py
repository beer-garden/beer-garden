# -*- coding: utf-8 -*-
import pytest
import tornado.web

from beer_garden.api.http import get_url_specs
from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.api.http.client import SerializeHelper
from beer_garden.db.mongo.models import User

application = tornado.web.Application(
    get_url_specs(prefix="/"),
    client=SerializeHelper(),
)


@pytest.fixture
def app():
    return application


@pytest.fixture
def user_without_permission():
    user = User(username="testuser").save()

    yield user
    user.delete()


@pytest.fixture
def access_token_not_permitted(user_without_permission):
    yield issue_token_pair(user_without_permission)["access"]
