import pytest
from brewtils.models import Command, Garden, Instance
from brewtils.models import Subscriber as BrewtilsSubscriber
from brewtils.models import System
from brewtils.models import Topic as BrewtilsTopic
from mock import Mock
from mongoengine import connect

from beer_garden import topic
from beer_garden.db.mongo.models import Topic
from beer_garden.topic import (
    create_topic,
    get_all_topics,
    get_topic,
    remove_topic,
    subscriber_match,
    topic_add_subscriber,
    topic_remove_subscriber,
)


@pytest.fixture(autouse=True)
def drop():
    yield
    Topic.drop_collection()


@pytest.fixture
def subscriber():
    return BrewtilsSubscriber(
        garden="bg",
        namespace="beer-garden",
        system="system",
        version="0.0.1",
        instance="inst",
        command="command",
    )


@pytest.fixture
def subscriber1():
    return BrewtilsSubscriber(
        garden="bg",
        namespace="beer-garden",
        system="system",
    )


@pytest.fixture
def subscriber2():
    return BrewtilsSubscriber(
        garden="bg",
        namespace="bg",
        system="system",
        version="0.0.1",
        instance="inst",
        command="command",
    )


@pytest.fixture
def subscriber3():
    return BrewtilsSubscriber(
        system="system",
        version="0.0.1",
        instance="inst",
        command="command",
    )


@pytest.fixture
def topic1():
    yield create_topic(BrewtilsTopic(name="foo"))


@pytest.fixture
def topic2():
    yield create_topic(BrewtilsTopic(name="bar"))


class TestTopic:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")

    def test_get_topic(self, topic1):
        """get_topic should allow for retrieval by name"""
        t = get_topic(topic1.id)

        assert type(t) is BrewtilsTopic
        assert t.id == topic1.id

    def test_get_all_topics(self, topic1, topic2):
        """get_all_topics should get all topics"""
        t = get_all_topics()
        assert len(t) == 2

    def test_upsert_subscriber(self, topic1, subscriber):
        """add subscriber to existing topic"""
        assert len(get_topic(topic1.id).subscribers) == 0
        new_topic = BrewtilsTopic(name=topic1.name, subscribers=[subscriber])
        create_topic(new_topic)
        assert len(get_topic(topic1.id).subscribers) == 1

    def test_remove_topic(self, topic1):
        """remove_topic should remove topic"""
        remove_topic(topic1.id)
        assert len(Topic.objects.filter(id=topic1.id)) == 0

    def test_add_subscriber(self, topic1, subscriber):
        """add subscriber to existing topic"""
        topic_add_subscriber(subscriber, topic1.id)
        assert len(get_topic(topic1.id).subscribers) == 1

    def test_remove_subscriber(self, topic2, subscriber):
        """remove subscriber from existing topic"""
        topic_add_subscriber(subscriber, topic2.id)
        topic_remove_subscriber(subscriber, topic2.id)
        assert len(get_topic(topic2.id).subscribers) == 0

    def test_subscriber_match(self, subscriber, subscriber1, subscriber2, subscriber3):
        """subscriber comparison"""
        assert (subscriber_match(subscriber, subscriber)) is True
        assert (subscriber_match(subscriber, subscriber1)) is True
        assert (subscriber_match(subscriber1, subscriber2)) is False
        assert (subscriber_match(subscriber1, subscriber3)) is True

    def test_prune_topics(self, monkeypatch):

        garden = Garden(
            name="garden",
            children=[],
            systems=[
                System(
                    name="local_system",
                    namespace="namespace",
                    version="1.2.3",
                    instances=[Instance(name="default")],
                    commands=[Command(name="command")],
                )
            ],
        )

        topics = [
            BrewtilsTopic(
                name="topic_1",
                subscribers=[
                    BrewtilsSubscriber(
                        garden="garden",
                        namespace="namespace",
                        system="system",
                        version="1.2.3",
                        instance="default",
                        command="command",
                        subscriber_type="ANNOTATED",
                    ),
                ],
            ),
        ]

        monkeypatch.setattr(topic, "get_all_topics", Mock(return_value=topics))

        mock_remove_topic = Mock(return_value=None)
        monkeypatch.setattr(topic, "remove_topic", mock_remove_topic)

        mock_update_topic = Mock(return_value=None)
        monkeypatch.setattr(topic, "update_topic", mock_update_topic)

        topic.prune_topics(garden)

        assert mock_remove_topic.call_count == 1
        assert mock_update_topic.call_count == 0

    def test_prune_topics_remove_one(self, monkeypatch):

        garden = Garden(
            name="garden",
            children=[],
            systems=[
                System(
                    name="system",
                    namespace="namespace",
                    version="1.2.3",
                    instances=[Instance(name="default")],
                    commands=[Command(name="command", topics=["topic_1"])],
                )
            ],
        )

        topics = [
            BrewtilsTopic(
                name="topic_1",
                subscribers=[
                    BrewtilsSubscriber(
                        garden="garden",
                        namespace="namespace",
                        system="system",
                        version="1.2.3",
                        instance="default",
                        command="command",
                        subscriber_type="ANNOTATED",
                    ),
                    BrewtilsSubscriber(
                        garden="other_garden",
                        namespace="other_namespace",
                        system="other_system",
                        version="1.2.3",
                        instance="other_default",
                        command="other_command",
                        subscriber_type="ANNOTATED",
                    ),
                ],
            ),
        ]

        monkeypatch.setattr(topic, "get_all_topics", Mock(return_value=topics))

        mock_remove_topic = Mock(return_value=None)
        monkeypatch.setattr(topic, "remove_topic", mock_remove_topic)

        mock_update_topic = Mock(return_value=None)
        monkeypatch.setattr(topic, "update_topic", mock_update_topic)

        topic.prune_topics(garden)

        assert mock_remove_topic.call_count == 0
        assert mock_update_topic.call_count == 1

    def test_prune_topics_remove_none(self, monkeypatch):

        garden = Garden(
            name="garden",
            children=[],
            systems=[
                System(
                    name="system",
                    namespace="namespace",
                    version="1.2.3",
                    instances=[Instance(name="default")],
                    commands=[Command(name="command", topics=["topic_2"])],
                )
            ],
        )

        topics = [
            BrewtilsTopic(
                name="topic_1",
                subscribers=[
                    BrewtilsSubscriber(
                        garden="garden",
                        namespace="namespace",
                        system="system",
                        version="1.2.3",
                        instance="default",
                        command="command",
                        subscriber_type="GENERATED",
                    ),
                    BrewtilsSubscriber(
                        garden="other_garden",
                        namespace="other_namespace",
                        system="other_system",
                        version="1.2.3",
                        instance="other_default",
                        command="other_command",
                        subscriber_type="DYNAMIC",
                    ),
                ],
            ),
        ]

        monkeypatch.setattr(topic, "get_all_topics", Mock(return_value=topics))

        mock_remove_topic = Mock(return_value=None)
        monkeypatch.setattr(topic, "remove_topic", mock_remove_topic)

        mock_update_topic = Mock(return_value=None)
        monkeypatch.setattr(topic, "update_topic", mock_update_topic)

        topic.prune_topics(garden)

        assert mock_remove_topic.call_count == 0
        assert mock_update_topic.call_count == 0
