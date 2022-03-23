# -*- coding: utf-8 -*-
import pytest
import tornado.web

from beer_garden.api.http.authentication import issue_token_pair
from beer_garden.api.http.client import SerializeHelper
from beer_garden.api.http.handlers.v1.admin import AdminAPI
from beer_garden.api.http.handlers.v1.command import CommandAPI, CommandListAPI
from beer_garden.api.http.handlers.v1.command_publishing_blocklist import (
    CommandPublishingBlocklistAPI,
    CommandPublishingBlocklistPathAPI,
)
from beer_garden.api.http.handlers.v1.forward import ForwardAPI
from beer_garden.api.http.handlers.v1.garden import GardenAPI, GardenListAPI
from beer_garden.api.http.handlers.v1.instance import (
    InstanceAPI,
    InstanceLogAPI,
    InstanceQueuesAPI,
)
from beer_garden.api.http.handlers.v1.job import (
    JobAPI,
    JobExecutionAPI,
    JobExportAPI,
    JobImportAPI,
    JobListAPI,
)
from beer_garden.api.http.handlers.v1.logging import LoggingAPI, LoggingConfigAPI
from beer_garden.api.http.handlers.v1.namespace import NamespaceListAPI
from beer_garden.api.http.handlers.v1.queue import QueueAPI, QueueListAPI
from beer_garden.api.http.handlers.v1.request import RequestAPI, RequestListAPI
from beer_garden.api.http.handlers.v1.role import RoleListAPI
from beer_garden.api.http.handlers.v1.system import SystemAPI, SystemListAPI
from beer_garden.api.http.handlers.v1.token import (
    TokenAPI,
    TokenRefreshAPI,
    TokenRevokeAPI,
)
from beer_garden.api.http.handlers.v1.user import (
    UserAPI,
    UserListAPI,
    UserPasswordChangeAPI,
)
from beer_garden.db.mongo.models import User

# TODO: Load this from conftest using the actual _setup_application call
application = tornado.web.Application(
    [
        (r"/api/v1/admin/?", AdminAPI),
        (r"/api/v1/commands/?", CommandListAPI),
        (r"/api/v1/config/logging/?", LoggingConfigAPI),
        (r"/api/v1/export/jobs/?", JobExportAPI),
        (r"/api/v1/import/jobs/?", JobImportAPI),
        (r"/api/v1/forward/?", ForwardAPI),
        (r"/api/v1/gardens/?", GardenListAPI),
        (r"/api/v1/gardens/(.*)/?", GardenAPI),
        (r"/api/v1/instances/(\w+)/?", InstanceAPI),
        (r"/api/v1/instances/(\w+)/logs/?", InstanceLogAPI),
        (r"/api/v1/instances/(\w+)/queues/?", InstanceQueuesAPI),
        (r"/api/v1/jobs/?", JobListAPI),
        (r"/api/v1/jobs/(\w+)/?", JobAPI),
        (r"/api/v1/jobs/(\w+)/execute/?", JobExecutionAPI),
        (r"/api/v1/logging/?", LoggingAPI),
        (r"/api/v1/password/change/?", UserPasswordChangeAPI),
        (r"/api/v1/token/?", TokenAPI),
        (r"/api/v1/token/revoke/?", TokenRevokeAPI),
        (r"/api/v1/token/refresh/?", TokenRefreshAPI),
        (r"/api/v1/namespaces/?", NamespaceListAPI),
        (r"/api/v1/queues/?", QueueListAPI),
        (r"/api/v1/queues/([\w\.-]+)/?", QueueAPI),
        (r"/api/v1/requests/?", RequestListAPI),
        (r"/api/v1/requests/(\w+)/?", RequestAPI),
        (r"/api/v1/roles/?", RoleListAPI),
        (r"/api/v1/systems/?", SystemListAPI),
        (r"/api/v1/systems/(\w+)/?", SystemAPI),
        (r"/api/v1/systems/(\w+)/commands/(\w+)/?", CommandAPI),
        (r"/api/v1/users/?", UserListAPI),
        (r"/api/v1/users/(\w+)/?", UserAPI),
        (r"/api/v1/commandpublishingblocklist/?", CommandPublishingBlocklistAPI),
        (
            r"/api/v1/commandpublishingblocklist/(\w+)/?",
            CommandPublishingBlocklistPathAPI,
        ),
    ],
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
