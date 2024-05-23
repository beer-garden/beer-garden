from typing import List

from brewtils.errors import PluginError
from brewtils.models import Events, Subscriber, Topic
from mongoengine import DoesNotExist

import beer_garden.db.api as db
from beer_garden.events import publish_event


@publish_event(Events.TOPIC_CREATED)
def create_topic(new_topic: Topic) -> Topic:
    """Creates a topic with the provided fields

    Args:
        topic: The topic to create
    Returns:
        Topic
    """
    try:
        topic = db.query_unique(Topic, name=new_topic.name, raise_missing=True)
        # If there are new subscribers, combine them
        if new_topic.subscribers:
            for subscriber in new_topic.subscribers:
                if subscriber not in topic.subscribers:
                    topic.subscribers.append(subscriber)
        return update_topic(topic)
    except DoesNotExist:
        return db.create(new_topic)


def get_topic(topic_id: str) -> Topic:
    """Retrieve an individual Topic

    Args:
        topic_id: The id of the Topic

    Returns:
        Topic
    """
    return db.query_unique(Topic, id=topic_id)


@publish_event(Events.TOPIC_REMOVED)
def remove_topic(topic_id: str = None, topic: Topic = None) -> Topic:
    """Remove a topic

    Args:
        topic_id: The Topic ID
        topic: The Topic

    Returns:
        The removed Topic

    """
    topic = topic or db.query_unique(Topic, id=topic_id)

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


def topic_add_subscriber(subscriber: Subscriber, topic_id: str) -> Topic:
    """Add a Subscriber to a Topic

    Args:
        subscriber: The subscriber to add
        topic_id: The Topic ID to add it to

    Returns:
        The updated Topic

    """
    try:
        topic = get_topic(topic_id)
    except DoesNotExist:
        raise PluginError(
            f"Topic '{topic_id}' does not exist, unable to map '{str(subscriber)}"
        )

    if subscriber not in topic.subscribers:
        topic.subscribers.append(subscriber)

    return update_topic(topic)


def topic_remove_subscriber(subscriber: Subscriber, topic_id: str) -> Topic:
    """Remove a Subscriber from a Topic

    Args:
        subscriber: The subscriber to remove
        topic_id: The Topic id to from it from

    Returns:
        The updated Topic
    """
    try:
        topic = get_topic(topic_id)
    except DoesNotExist:
        raise PluginError(
            f"Topic '{topic_id}' does not exist, unable to map '{str(subscriber)}"
        )

    if subscriber in topic.subscribers:
        topic.subscribers.remove(subscriber)

    return update_topic(topic)


@publish_event(Events.TOPIC_UPDATED)
def update_topic(topic: Topic) -> Topic:
    """Update a Topic

    Args:
        topic: The Topic to update

    Returns:
        The updated Topic
    """
    return db.update(topic)


def subscriber_match(
    first_subscriber: Subscriber, second_subscriber: Subscriber
) -> bool:
    match = False
    for item in ["garden", "namespace", "system", "version", "instance", "command"]:
        first_value = getattr(first_subscriber, item)
        second_value = getattr(second_subscriber, item)
        if first_value and second_value:
            if first_value == second_value:
                match = True
            else:
                return False

    return match
