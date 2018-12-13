import pytest
from mock import Mock, MagicMock
from mongoengine import connect

import brew_view
from brew_view.authorization import anonymous_principal
from test.utils import brew2mongo

pytest_plugins = [
    'brewtils.test.conftest',
]


@pytest.fixture
def config():
    c = MagicMock()

    c.auth.enabled = False
    c.web.url_prefix = '/'

    return c


@pytest.fixture()
def mongo():
    connect('beer_garden', host='mongomock://localhost')


@pytest.fixture
def app(monkeypatch, config, mongo):
    monkeypatch.setattr(brew_view, '_load_swagger', Mock())
    monkeypatch.setattr(brew_view, 'event_publishers', MagicMock())
    monkeypatch.setattr(brew_view, 'config', config)
    monkeypatch.setattr(brew_view, 'anonymous_principal', anonymous_principal())

    application = brew_view._setup_tornado_app()

    return application


@pytest.fixture
def thrift_client():
    return Mock(name="Thrift Client")


@pytest.fixture
def thrift_context(thrift_client):
    return MagicMock(
        __enter__=Mock(return_value=thrift_client),
        __exit__=Mock(return_value=False),
    )


@pytest.fixture
def mongo_system(bg_system):
    return brew2mongo(bg_system)
