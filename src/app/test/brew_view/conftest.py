import pytest
from mock import Mock, MagicMock
from mongoengine import connect

import beer_garden.brew_view as bv
import brewtils.test
from beer_garden.bg_utils.mongo.parser import MongoParser
from beer_garden.brew_view.authorization import anonymous_principal
from test.brew_view.utils import brew2mongo


def pytest_configure():
    setattr(brewtils.test, "_running_tests", True)


def pytest_unconfigure():
    delattr(brewtils.test, "_running_tests")


@pytest.fixture
def config():
    c = MagicMock()

    c.auth.enabled = False
    c.web.url_prefix = "/"

    return c


@pytest.fixture()
def mongo():
    connect("beer_garden", host="mongomock://localhost")


@pytest.fixture
def app(monkeypatch, config, mongo, event_publishers):
    monkeypatch.setattr(brew_view, "_load_swagger", Mock())
    monkeypatch.setattr(brew_view, "event_publishers", event_publishers)
    monkeypatch.setattr(brew_view, "config", config)
    monkeypatch.setattr(brew_view, "anonymous_principal", anonymous_principal())

    application = brew_view._setup_tornado_app()

    return application


@pytest.fixture
def event_publishers():
    from bg_utils.event_publisher import EventPublishers

    return EventPublishers(connections={"mock": MagicMock()})


@pytest.fixture
def thrift_client():
    return Mock(name="Thrift Client")


@pytest.fixture
def thrift_context(thrift_client):
    return Mock(
        return_value=MagicMock(
            name="Thrift Context",
            __enter__=Mock(return_value=thrift_client),
            __exit__=Mock(return_value=False),
        )
    )


@pytest.fixture
def mongo_system(bg_system):
    return brew2mongo(bg_system)


@pytest.fixture
def mongo_job(bg_job):
    return brew2mongo(bg_job)


@pytest.fixture
def mongo_principal(principal_dict):
    principal = principal_dict.copy()
    del principal["permissions"]
    return MongoParser().parse_principal(principal, False)


@pytest.fixture
def mongo_role(role_dict):
    role = role_dict.copy()
    role["roles"] = []
    return MongoParser().parse_role(role, False)


@pytest.fixture
def mongo_bg_request(bg_request):
    return brew2mongo(bg_request)


@pytest.fixture
def mongo_parent_request(parent_request):
    return brew2mongo(parent_request)


@pytest.fixture
def mongo_child_request(child_request):
    return brew2mongo(child_request)
