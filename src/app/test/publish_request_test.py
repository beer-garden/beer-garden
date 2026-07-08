import pytest
from brewtils.models import (
    Command,
    Event,
    Events,
    Garden,
    Instance,
    Request,
    Subscriber,
    System,
    Topic,
)
from mock import Mock
from mongoengine.connection import get_db

from beer_garden import config, publish_request


@pytest.fixture(autouse=True)
def drop():
    yield
    db = get_db()
    for collection in db.list_collection_names():
        db[collection].drop()


@pytest.fixture
def command_topic_one():
    return Command(name="command_one_topic", topics=["topic_1"])


@pytest.fixture
def command_topic_two():
    return Command(name="command_two_topic", topics=["topic_1", "topic_2"])


@pytest.fixture
def command_topic_any():
    return Command(name="command_any_topic", topics=["topic.*"])


@pytest.fixture
def localgarden_system(command_topic_one, command_topic_two, command_topic_any):
    return System(
        name="localsystem",
        version="1.2.3",
        namespace="localgarden",
        local=True,
        instances=[Instance(name="default", status="RUNNING")],
        commands=[command_topic_one, command_topic_two, command_topic_any],
    )


@pytest.fixture
def localgarden_system_2(command_topic_one, command_topic_two, command_topic_any):
    return System(
        name="localsystem",
        version="1.2.4",
        namespace="localgarden",
        local=True,
        instances=[Instance(name="default", status="RUNNING")],
        commands=[command_topic_one, command_topic_two, command_topic_any],
    )


@pytest.fixture
def localgarden(localgarden_system, localgarden_system_2):
    return Garden(
        name="localgarden",
        connection_type="LOCAL",
        systems=[localgarden_system, localgarden_system_2],
    )


@pytest.fixture
def topic_1():
    return Topic(
        name="topic_1",
        subscribers=[
            Subscriber(
                garden="localgarden",
                namespace="localgarden",
                system="localsystem",
                version="1.2.3",
                instance="default",
                command="command_one_topic",
                subscriber_type="DYNAMIC",
            ),
            Subscriber(
                garden="localgarden",
                namespace="localgarden",
                system="localsystem",
                version="1.2.4",
                instance="default",
                command="command_two_topic",
                subscriber_type="DYNAMIC",
            ),
        ],
    )


@pytest.fixture
def topic_2():
    return Topic(
        name="topic_2",
        subscribers=[
            Subscriber(
                garden="localgarden",
                namespace="localgarden",
                system="localsystem",
                version="1.2.5",
                instance="default",
                command="command_two_topic",
                subscriber_type="DYNAMIC",
            )
        ],
    )


@pytest.fixture
def topic_wildcard():
    return Topic(
        name="topic.*",
        subscribers=[
            Subscriber(
                garden=".*",
                namespace=None,
                system="",
                version="1.2.\\d+",
                instance="def.*",
                command="command_any_topic",
                subscriber_type="DYNAMIC",
            )
        ],
    )


class TestSubscriptionEvent(object):

    def test_newtopic(self, monkeypatch, localgarden):
        mock_route_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "route_request", mock_route_request)
        monkeypatch.setattr(publish_request, "get_topics_regex", Mock(return_value=[]))
        monkeypatch.setattr(
            publish_request, "get_systems_regex", Mock(return_value=localgarden.systems)
        )
        monkeypatch.setattr(
            publish_request, "get_garden_name", Mock(return_value=localgarden.name)
        )

        config._CONFIG = {"garden": {"name": localgarden.name}}
        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"_propagate": False, "topic": "newtopic"},
            garden=localgarden.name,
            payload=Request(),
        )

        publish_request.handle_event(event)

        assert mock_route_request.call_count == 0

    def test_topic_one(self, monkeypatch, topic_1, localgarden):
        mock_route_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "route_request", mock_route_request)
        monkeypatch.setattr(
            publish_request, "get_topics_regex", Mock(return_value=[topic_1])
        )
        monkeypatch.setattr(
            publish_request, "get_systems_regex", Mock(return_value=localgarden.systems)
        )
        monkeypatch.setattr(
            publish_request, "get_garden_name", Mock(return_value=localgarden.name)
        )

        config._CONFIG = {"garden": {"name": localgarden.name}}

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"_propagate": False, "topic": "topic_1"},
            garden=localgarden.name,
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_route_request.call_count == 2

    def test_topic_two(self, monkeypatch, topic_2, localgarden):
        mock_route_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "route_request", mock_route_request)
        monkeypatch.setattr(
            publish_request, "get_topics_regex", Mock(return_value=[topic_2])
        )
        monkeypatch.setattr(
            publish_request, "get_systems_regex", Mock(return_value=localgarden.systems)
        )
        monkeypatch.setattr(
            publish_request, "get_garden_name", Mock(return_value=localgarden.name)
        )
        config._CONFIG = {"garden": {"name": localgarden.name}}

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"_propagate": False, "topic": "topic_2"},
            garden=localgarden.name,
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_route_request.call_count == 0

    def test_topic_wildcard(self, monkeypatch, topic_wildcard, localgarden):
        mock_route_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "route_request", mock_route_request)
        monkeypatch.setattr(
            publish_request,
            "get_topics_regex",
            Mock(
                return_value=[
                    topic_wildcard,
                ]
            ),
        )
        monkeypatch.setattr(
            publish_request, "get_systems_regex", Mock(return_value=localgarden.systems)
        )
        monkeypatch.setattr(
            publish_request, "get_garden_name", Mock(return_value=localgarden.name)
        )
        config._CONFIG = {"garden": {"name": localgarden.name}}

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"_propagate": False, "topic": "topic_3"},
            garden=localgarden.name,
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_route_request.call_count == 2

    def test_topic_one_not_local(self, monkeypatch, topic_wildcard, localgarden):
        mock_route_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "route_request", mock_route_request)
        monkeypatch.setattr(
            publish_request, "get_topics_regex", Mock(return_value=[topic_wildcard])
        )
        monkeypatch.setattr(
            publish_request, "get_systems_regex", Mock(return_value=localgarden.systems)
        )
        monkeypatch.setattr(
            publish_request, "get_garden_name", Mock(return_value=localgarden.name)
        )

        config._CONFIG = {"garden": {"name": localgarden.name}}

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"_propagate": False, "topic": "topic_1"},
            garden="remote_garden",
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_route_request.call_count == 0

    def test_topic_one_not_local_propagate(self, monkeypatch, topic_1, localgarden):
        mock_route_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "route_request", mock_route_request)
        monkeypatch.setattr(
            publish_request, "get_topics_regex", Mock(return_value=[topic_1])
        )
        monkeypatch.setattr(
            publish_request, "get_systems_regex", Mock(return_value=localgarden.systems)
        )
        monkeypatch.setattr(
            publish_request, "get_garden_name", Mock(return_value=localgarden.name)
        )

        config._CONFIG = {"garden": {"name": localgarden.name}}

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"propagate": True, "topic": "topic_1"},
            garden="remote_garden",
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_route_request.call_count == 2
