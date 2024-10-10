import logging
from typing import List

from brewtils.errors import PluginError
from brewtils.models import Event, Events, Garden, Subscriber, Topic
from mongoengine import DoesNotExist

import beer_garden.config as config
import beer_garden.db.api as db

logger = logging.getLogger(__name__)


# TODO: Add Publish Events back when UI supports it
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


def get_topic(topic_id: str = None, topic_name: str = None) -> Topic:
    """Retrieve an individual Topic

    Args:
        topic_id: The id of the Topic
        topic_name: The name of the Topic

    Returns:
        Topic
    """
    if topic_id:
        return db.query_unique(Topic, id=topic_id)
    return db.query_unique(Topic, name=topic_name)


def remove_topic(
    topic_id: str = None, topic_name: str = None, topic: Topic = None
) -> Topic:
    """Remove a topic

    Args:
        topic_id: The Topic ID
        topic: The Topic

    Returns:
        The removed Topic

    """
    if not topic:
        topics = []
        if topic_id:
            topics = db.query(
                Topic,
                filter_params={"id": topic_id},
            )
        elif topic_name:
            topics = db.query(
                Topic,
                filter_params={"name": topic_name},
            )

        if topics:
            topic = topics[0]
        else:
            logger.error(
                (
                    "Attempted to delete topic not found in database, "
                    f"{'ID: ' + topic_id if topic_id else 'Name: ' + topic_name}"
                )
            )
            return None

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


def topic_add_subscriber(
    subscriber: Subscriber, topic_id: str = None, topic_name: str = None
) -> Topic:
    """Add a Subscriber to a Topic

    Args:
        subscriber: The subscriber to add
        topic_id: The Topic ID to add it to

    Returns:
        The updated Topic

    """
    topic = get_topic(topic_id=topic_id, topic_name=topic_name)

    if topic is None:
        if topic_name:
            topic = create_topic(Topic(name=topic_name))
        else:
            raise PluginError(
                f"Topic '{topic_id}' does not exist, unable to map '{str(subscriber)}"
            )

    if subscriber not in topic.subscribers:
        topic.subscribers.append(subscriber)

    return update_topic(topic)


def topic_remove_subscriber(
    subscriber: Subscriber, topic_id: str = None, topic_name: str = None
) -> Topic:
    """Remove a Subscriber from a Topic

    Args:
        subscriber: The subscriber to remove
        topic_id: The Topic id to from it from

    Returns:
        The updated Topic
    """
    topic = get_topic(topic_id=topic_id, topic_name=topic_name)

    if topic is None:
        raise PluginError(
            f"Topic '{topic_id}' does not exist, unable to map '{str(subscriber)}"
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


def prune_topics(garden):
    for topic in get_all_topics():
        if topic.subscribers:
            valid_subscribers = []
            update_subscribers = False
            for subscriber in topic.subscribers:
                if subscriber.subscriber_type == "DYNAMIC" or subscriber_validate(
                    subscriber, garden, topic.name
                ):
                    valid_subscribers.append(subscriber)
                else:
                    update_subscribers = True
                    logger.debug(f"Removing Subscriber {subscriber}")
            if update_subscribers:
                if len(valid_subscribers) == 0:
                    logger.debug(f"Removing Topic {topic.name}")
                    remove_topic(topic_name=topic.name)
                else:
                    topic.subscribers = valid_subscribers
                    update_topic(topic)


def subscriber_validate(
    subscriber: Subscriber, garden: Garden, topic_name: str
) -> bool:
    if subscriber.garden == garden.name:
        for system in garden.systems:
            if (
                subscriber.system == system.name
                and subscriber.version == system.version
            ):
                for instance in system.instances:
                    if subscriber.instance == instance.name:
                        for command in system.commands:
                            if subscriber.command == command.name:
                                if subscriber.subscriber_type == "GENERATED":
                                    return True
                                if (
                                    subscriber.subscriber_type == "ANNOTATED"
                                    and topic_name in command.topics
                                ):
                                    return True

    if garden.children:
        for child in garden.children:
            if subscriber_validate(subscriber, child, topic_name):
                return True
    return False


def create_garden_topics(garden: Garden):
    for system in garden.systems:
        default_topic = system.prefix_topic
        for command in system.commands:
            for instance in system.instances:
                if len(command.topics) > 0:
                    for topic in command.topics:
                        create_topic(
                            Topic(
                                name=topic,
                                subscribers=[
                                    Subscriber(
                                        garden=garden.name,
                                        namespace=system.namespace,
                                        system=system.name,
                                        version=system.version,
                                        instance=instance.name,
                                        command=command.name,
                                        subscriber_type="ANNOTATED",
                                    )
                                ],
                            )
                        )

                if not default_topic:
                    topic_generated = (
                        f"{system.namespace}.{system.name}."
                        f"{system.version}.{instance.name}."
                        f"{command.name}"
                    )
                else:
                    topic_generated = f"{default_topic}.{command.name}"

                create_topic(
                    Topic(
                        name=topic_generated,
                        subscribers=[
                            Subscriber(
                                garden=garden.name,
                                namespace=system.namespace,
                                system=system.name,
                                version=system.version,
                                instance=instance.name,
                                command=command.name,
                                subscriber_type="GENERATED",
                            )
                        ],
                    )
                )

    for child in garden.children:
        create_garden_topics(child)


def increase_publish_count(topic: Topic):
    return db.modify(topic, inc__publisher_count=1)


def increase_consumer_count(topic: Topic, subscriber: Subscriber):
    db_topic = get_topic(topic_id=topic.id)

    for db_subscriber in db_topic.subscribers:
        if db_subscriber == subscriber:
            db_subscriber.consumer_count += 1
            break

    updated = db.update(db_topic)
    return updated


def handle_event(event: Event) -> None:
    """Handle TOPIC events

    When creating or updating a system, make sure to mark as non-local first.

    It's possible that we see SYSTEM_UPDATED events for systems that we don't currently
    know about. This will happen if a new system is created on the child while the child
    is operating in standalone mode. To handle that, just create the system.

    Args:
        event: The event to handle
    """

    if event.garden == config.get("garden.name"):
        if event.name == Events.GARDEN_SYNC.name:
            create_garden_topics(event.payload)
            prune_topics(event.payload)
