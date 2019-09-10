import pytest
from mock import Mock, MagicMock
from mongoengine import connect

import beer_garden.brew_view as bv
from beer_garden.brew_view.authorization import anonymous_principal


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
