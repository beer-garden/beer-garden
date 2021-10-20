import pytest
from mock import MagicMock, Mock
from mongoengine import connect

import beer_garden.api.http as bv


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
def app(monkeypatch, config, mongo):
    monkeypatch.setattr(bv, "_load_swagger", Mock())
    monkeypatch.setattr(bv, "event_publishers", event_publishers)
    monkeypatch.setattr(bv, "config", config)

    application = bv._setup_tornado_app()

    return application


@pytest.fixture
def event_publishers():
    from beer_garden.bg_utils.event_publisher import EventPublishers

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
