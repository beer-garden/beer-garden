import pytest
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import Garden as BrewtilsGarden
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import Subscriber as BrewtilsSubscriber
from brewtils.models import System as BrewtilsSystem
from brewtils.models import Topic as BrewtilsTopic

import beer_garden
from beer_garden.db.mongo.models import Garden, System, Topic
from beer_garden.garden import create_garden
from beer_garden.systems import create_system, remove_system
from beer_garden.topic import (
    create_topic,
    get_all_topics,
    get_topic,
    increase_consumer_count,
    increase_publish_count,
    prune_topics,
    remove_topic,
    subscriber_match,
    sync_topics_batch,
    topic_add_subscriber,
    topic_remove_subscriber,
)


@pytest.fixture(autouse=True)
def drop():
    yield
    Topic.drop_collection()
    Garden.drop_collection()
    System.drop_collection()


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


@pytest.fixture
def local_garden_system():
    yield create_system(
        BrewtilsSystem(
            name="local_system",
            version="1.2.3",
            namespace="local_garden",
            local=True,
            instances=[BrewtilsInstance(name="1")],
            commands=[BrewtilsCommand(name="command")],
        )
    )


@pytest.fixture
def local_garden(local_garden_system):
    yield create_garden(
        BrewtilsGarden(
            name="local_garden",
            connection_type="LOCAL",
            systems=[local_garden_system],
            version=beer_garden.__version__,
        )
    )


@pytest.fixture
def remote_garden():
    yield create_garden(
        BrewtilsGarden(
            name="remote_garden",
            connection_type="REMOTE",
            systems=[
                BrewtilsSystem(
                    name="remote_system",
                    version="1.2.3",
                    namespace="remote_garden",
                    garden_name="remote_garden",
                    local=False,
                    instances=[BrewtilsInstance(name="1")],
                    commands=[BrewtilsCommand(name="command")],
                )
            ],
            version=beer_garden.__version__,
        )
    )


class TestTopic:

    def test_get_topic_id(self, topic1):
        """get_topic should allow for retrieval by name"""
        t = get_topic(topic_id=topic1.id)

        assert type(t) is BrewtilsTopic
        assert t.id == topic1.id

    def test_get_topic_name(self, topic1):
        """get_topic should allow for retrieval by name"""
        t = get_topic(topic_name=topic1.name)

        assert type(t) is BrewtilsTopic
        assert t.name == topic1.name

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

    def test_remove_topic_id(self, topic1):
        """remove_topic should remove topic"""
        remove_topic(topic_id=topic1.id)
        assert len(Topic.objects.filter(id=topic1.id)) == 0

    def test_remove_topic_name(self, topic1):
        """remove_topic should remove topic"""
        remove_topic(topic_name=topic1.name)
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

    def test_sync_batched(self, local_garden):

        topics_generated = Topic.objects().count()
        assert topics_generated == 1
        Topic.drop_collection()

        topics_generated = Topic.objects().count()
        assert topics_generated == 0

        sync_topics_batch()
        topics_generated = Topic.objects().count()
        assert topics_generated == 1

    def test_topic_prune(self, local_garden):

        System.drop_collection()
        Garden.drop_collection()

        topics_generated = Topic.objects().count()
        assert topics_generated == 1

        prune_topics()
        topics_generated = Topic.objects().count()
        assert topics_generated == 0

    def test_remote_no_topics(self, remote_garden):

        topics_generated = Topic.objects().count()
        assert topics_generated == 0

    def test_background_system_topic_prune(self, local_garden_system):

        topics_generated = Topic.objects().count()
        assert topics_generated == 1

        remove_system(system=local_garden_system)

        topics_generated = Topic.objects().count()
        assert topics_generated == 0

    def test_increase_topic_counter(self, topic1):
        assert topic1.publisher_count == 0

        increase_publish_count(topic1)

        db_topic = get_topic(topic_id=topic1.id)
        assert db_topic.publisher_count == 1

    def test_increase_subscriber_counter(self, topic1, subscriber):
        topic_add_subscriber(subscriber, topic1.id)

        increase_consumer_count(topic1, subscriber)

        db_topic = get_topic(topic_id=topic1.id)

        assert db_topic.subscribers[0].consumer_count == 1
