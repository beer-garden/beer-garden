from brewtils.models import Topic, Subscriber
from typing import List

import beer_garden.db.api as db
from mongoengine import DoesNotExist
from brewtils.errors import PluginError


def create_topic(topic: Topic) -> Topic:
    """Creates a topic with the provided fields

    Args:
        topic: The topic to create
    Returns:
        Topic
    """
    topic = db.create(topic)
    return topic


def get_topic(topic_name: str) -> Topic:
    """Retrieve an individual Topic

    Args:
        topic_name: The name of the Topic

    Returns:
        Topic
    """
    topic = db.query_unique(Topic, name=topic_name, raise_missing=True)
    return topic


def delete_topic(topic_name: str = None, topic: Topic = None) -> Topic:
    """Remove a topic

    Args:
        topic_name: The Topic name

    Returns:
        The deleted topic
    """

    topic = topic or get_topic(topic_name)

    db.delete(topic)

    return topic


def get_all_topics(**kwargs) -> List[Topic]:
    """Retrieve list of all Topics

    Keyword Args:
        Parameters to be passed to the DB query

    Returns:
        All known topics

    """
    return db.query(Topic, **kwargs)


def topic_add_subscriber(subscriber: Subscriber, topic_name: str) -> Topic:
    """Add a Subscriber to a Topic

    Args:
        subscriber: The subscriber to add
        topic_name: The Topic Name to add it to

    Returns:
        The updated Topic

    """
    try:
        topic = get_topic(topic_name)
    except DoesNotExist:
        raise PluginError(
            f"Topic '{topic_name}' does not exist, unable to map '{str(subscriber)}"
        )

    if subscriber not in topic.subscribers:
        topic.subscribers.append(subscriber)

    # return update_topic(topic)
    return update_topic(topic)


def topic_remove_subscriber(subscriber: Subscriber, topic_name: str) -> Topic:
    """Remove a Subscriber from a Topic

    Args:
        subscriber: The subscriber to remove
        topic_name: The Topic Name to from it from

    Returns:
        The updated Topic

    """
    try:
        topic = get_topic(topic_name)
    except DoesNotExist:
        raise PluginError(
            f"Topic '{topic_name}' does not exist, unable to map '{str(subscriber)}"
        )

    if subscriber in topic.subscribers:
        topic.subscribers.remove(subscriber)

    return update_topic(topic)


def update_topic(topic: Topic) -> Topic:
    """Update a Topic

    Args:
        topic: The Topic to update

    Returns:
        The updated Topic
    """
    return db.update(topic)
