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

from beer_garden import publish_request
from beer_garden.db.mongo.models import Topic as DB_Topic
from beer_garden.topic import create_topic


@pytest.fixture(autouse=True)
def drop():
    yield
    DB_Topic.drop_collection()


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
def localgarden(localgarden_system):
    return Garden(
        name="localgarden", connection_type="LOCAL", systems=[localgarden_system]
    )


@pytest.fixture
def topics():
    return [
        create_topic(
            Topic(
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
                        version="1.2.3",
                        instance="default",
                        command="command_two_topic",
                        subscriber_type="DYNAMIC",
                    ),
                ],
            )
        ),
        create_topic(
            Topic(
                name="topic_2",
                subscribers=[
                    Subscriber(
                        garden="localgarden",
                        namespace="localgarden",
                        system="localsystem",
                        version="1.2.3",
                        instance="default",
                        command="command_two_topic",
                        subscriber_type="DYNAMIC",
                    )
                ],
            )
        ),
        create_topic(
            Topic(
                name="topic.*",
                subscribers=[
                    Subscriber(
                        garden="localgarden",
                        namespace="localgarden",
                        system="localsystem",
                        version="1.2.3",
                        instance="default",
                        command="command_any_topic",
                        subscriber_type="DYNAMIC",
                    )
                ],
            )
        ),
    ]


class TestSubscriptionEvent(object):
    def test_newtopic(self, monkeypatch, topics, localgarden):
        mock_process_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "process_request", mock_process_request)
        monkeypatch.setattr(
            publish_request, "get_all_topics", Mock(return_value=topics)
        )
        monkeypatch.setattr(
            publish_request, "local_garden", Mock(return_value=localgarden)
        )

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"propagate": False, "topic": "newtopic"},
            payload=Request(),
        )

        publish_request.handle_event(event)

        assert mock_process_request.call_count == 0

    def test_topic_one(self, monkeypatch, topics, localgarden):
        mock_process_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "process_request", mock_process_request)

        monkeypatch.setattr(
            publish_request, "get_all_topics", Mock(return_value=topics)
        )
        monkeypatch.setattr(
            publish_request, "local_garden", Mock(return_value=localgarden)
        )

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"propagate": False, "topic": "topic_1"},
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_process_request.call_count == 3

    def test_topic_two(self, monkeypatch, topics, localgarden):
        mock_process_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "process_request", mock_process_request)
        monkeypatch.setattr(
            publish_request, "get_all_topics", Mock(return_value=topics)
        )
        monkeypatch.setattr(
            publish_request, "local_garden", Mock(return_value=localgarden)
        )

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"propagate": False, "topic": "topic_2"},
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_process_request.call_count == 2

    def test_topic_wildcard(self, monkeypatch, topics, localgarden):
        mock_process_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "process_request", mock_process_request)
        monkeypatch.setattr(
            publish_request, "get_all_topics", Mock(return_value=topics)
        )
        monkeypatch.setattr(
            publish_request, "local_garden", Mock(return_value=localgarden)
        )

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"propagate": False, "topic": "topic_3"},
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_process_request.call_count == 1

    def test_topic_start_substring(self, monkeypatch, topics, localgarden):
        mock_process_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "process_request", mock_process_request)
        monkeypatch.setattr(
            publish_request, "get_all_topics", Mock(return_value=topics)
        )
        monkeypatch.setattr(
            publish_request, "local_garden", Mock(return_value=localgarden)
        )

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"propagate": False, "topic": "topic"},
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_process_request.call_count == 1

    def test_topic_non_match(self, monkeypatch, topics, localgarden):
        mock_process_request = Mock(return_value=None)
        monkeypatch.setattr(publish_request, "process_request", mock_process_request)
        monkeypatch.setattr(
            publish_request, "get_all_topics", Mock(return_value=topics)
        )
        monkeypatch.setattr(
            publish_request, "local_garden", Mock(return_value=localgarden)
        )

        event = Event(
            name=Events.REQUEST_TOPIC_PUBLISH.name,
            metadata={"propagate": False, "topic": "badTopic"},
            payload=Request(),
        )
        publish_request.handle_event(event)

        assert mock_process_request.call_count == 0
