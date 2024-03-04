import pytest
from mongoengine import connect

from brewtils.models import Topic as BrewtilsTopic
from brewtils.models import Subscriber as BrewtilsSubscriber
from beer_garden.topic import (
    create_topic,
    get_topic,
    delete_topic,
    get_all_topics,
    topic_add_subscriber,
    topic_remove_subscriber,
)
from beer_garden.db.mongo.models import Topic
from mongoengine import DoesNotExist


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
        t = get_topic(topic1.name)

        assert type(t) is BrewtilsTopic
        assert t.name == topic1.name

    def test_get_all_topics(self, topic1, topic2):
        """get_all_topics should get all topics"""
        t = get_all_topics()
        assert len(t) == 2

    def test_remove_topic(self, topic1):
        """delete_topic should remove topic"""
        delete_topic(topic1.name)

        assert len(Topic.objects.filter(name=topic1.name)) == 0
        with pytest.raises(DoesNotExist):
            get_topic(topic1.name)

    def test_add_subscriber(self, topic1, subscriber):
        """add subscriber to existing topic"""
        topic_add_subscriber(subscriber, topic1.name)
        assert len(get_topic(topic1.name).subscribers) == 1

    def test_remove_subscriber(self, topic2, subscriber):
        """remove subscriber from existing topic"""
        topic_add_subscriber(subscriber, topic2.name)
        topic_remove_subscriber(subscriber, topic2.name)
        assert len(get_topic(topic2.name).subscribers) == 0
