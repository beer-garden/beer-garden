import pytest
from brewtils.models import Subscriber as BrewtilsSubscriber
from brewtils.models import Topic as BrewtilsTopic
from mongoengine import connect

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
