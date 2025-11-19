import copy
import logging
from typing import List

from brewtils.errors import PluginError
from brewtils.models import Event, Garden, Subscriber, System, Topic
from mongoengine import DoesNotExist

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
        do_update = False
        if new_topic.subscribers:
            for subscriber in new_topic.subscribers:
                if subscriber not in topic.subscribers:
                    topic.subscribers.append(subscriber)
                    do_update = True
        if do_update:
            return update_topic(topic)
        return topic
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


def get_topics_regex(topic) -> List[Topic]:
    """Based off provided topic find matching regex contained within the Topics table

    Args:
        topic: Topic to match

    Return:
        list[Topic]: List of matching topics based on regex within the table
    """

    return db.query(
        Topic, raw_query={"$expr": {"$regexMatch": {"input": topic, "regex": "$name"}}}
    )


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


def topic_has_system_subscribers(topic: Topic, system: System):
    for subscriber in topic.subscribers:
        if (
            subscriber.system == system.name
            and subscriber.namespace == system.namespace
            and subscriber.version == system.version
        ):
            return True
    return False


def subscriber_validate(
    subscriber: Subscriber, garden: Garden, topic_name: str
) -> bool:
    if subscriber.garden == garden.name:
        if subscriber_systems_validate(subscriber, garden.systems, topic_name):
            return True

    if garden.children:
        for child in garden.children:
            if subscriber_validate(subscriber, child, topic_name):
                return True
    return False


def subscriber_system_validate(subscriber, system):
    if (
        subscriber.system == system.name
        and subscriber.namespace == system.namespace
        and subscriber.version == system.version
    ):
        return False
    return True


def subscriber_systems_validate(subscriber, systems, topic_name: str):
    for system in systems:
        if subscriber.system == system.name and subscriber.version == system.version:
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


def sync_topics():

    logger.info("Running Topic Sync")

    updated_subscribers, created_topics = sync_topics_batch()

    deleted_topic_count, deleted_subscriber_count = prune_topics()

    if (
        updated_subscribers > 0
        or created_topics > 0
        or deleted_topic_count > 0
        or deleted_subscriber_count > 0
    ):
        logger.info(
            (
                "Topic Sync: "
                f"Updated Subscribers {updated_subscribers}, "
                f"Deleted Subscribers {deleted_subscriber_count}, "
                f"Created Topics {created_topics}, "
                f"Deleted Topics {deleted_topic_count}"
            )
        )


def prune_topics():
    return db.prune_topics()


def sync_garden_topic_add(subscriber: Subscriber, topic_name: str, topics_dict: dict):
    """
    Add a subscriber to a topic in the topics dictionary. If the topic already exists,
    the subscriber is added to the list of subscribers for that topic if they are not
    already present. If the topic does not exist, a new topic is created with the
    subscriber as the initial subscriber.

    Args:
        subscriber (Subscriber): The subscriber to add to the topic.
        topic_name (str): The name of the topic to which the subscriber should be added.
        topics_dict (dict): A dictionary where the keys are topic names and the values
                            are Topic objects.

    Returns:
        None
    """
    updated_subscribers = 0
    created_topics = 0
    if topic_name in topics_dict:
        if subscriber not in topics_dict[topic_name].subscribers:
            topics_dict[topic_name].subscribers.append(subscriber)
            update_topic(topics_dict[topic_name])
            updated_subscribers = updated_subscribers + 1

    else:
        topics_dict[topic_name] = create_topic(
            Topic(name=topic_name, subscribers=[subscriber])
        )
        created_topics = created_topics + 1

    return updated_subscribers, created_topics


def sync_topics_batch():
    """
    Synchronizes topics for all systems, commands, and instances.

    This function iterates through all systems, and for each system,
    it iterates through its commands and instances to create topics. If a command has predefined
    topics, it creates topics for each one. If not, it generates a default topic based on the
    system's namespace, name, version, instance name, and command name. It then creates a topic
    with the generated name.

    Returns:
        None
    """

    cached_topics = {}
    updated_subscribers, created_topics = 0, 0
    for topic in get_all_topics():
        cached_topics[topic.name] = {"topic": topic, "updated": False}

    for system in db.query(
        System,
        include_fields=[
            "garden_name",
            "namespace",
            "name",
            "version",
            "prefix_topic",
            "instances.name",
            "commands.topics",
            "commands.name",
        ],
    ):
        default_topic = system.prefix_topic
        for command in system.commands:
            for instance in system.instances:
                if len(command.topics) > 0:
                    for topic in command.topics:
                        subscriber = Subscriber(
                            garden=system.garden_name,
                            namespace=system.namespace,
                            system=system.name,
                            version=system.version,
                            instance=instance.name,
                            command=command.name,
                            subscriber_type="ANNOTATED",
                        )

                        if topic not in cached_topics:
                            cached_topics[topic] = {
                                "topic": Topic(
                                    name=topic, subscribers=[copy.deepcopy(subscriber)]
                                ),
                                "updated": True,
                            }
                            created_topics = created_topics + 1

                        elif (
                            subscriber not in cached_topics[topic]["topic"].subscribers
                        ):
                            cached_topics[topic]["topic"].subscribers.append(
                                copy.deepcopy(subscriber)
                            )
                            cached_topics[topic]["updated"] = True
                            updated_subscribers = updated_subscribers + 1

                if not default_topic:
                    topic_generated = (
                        f"{system.garden_name}.{system.namespace}."
                        f"{system.name}.{system.version}."
                        f"{instance.name}.{command.name}"
                    )
                else:
                    topic_generated = f"{default_topic}.{command.name}"

                subscriber = Subscriber(
                    garden=system.garden_name,
                    namespace=system.namespace,
                    system=system.name,
                    version=system.version,
                    instance=instance.name,
                    command=command.name,
                    subscriber_type="GENERATED",
                )

                if topic_generated not in cached_topics:
                    cached_topics[topic_generated] = {
                        "topic": Topic(
                            name=topic_generated,
                            subscribers=[copy.deepcopy(subscriber)],
                        ),
                        "updated": True,
                    }
                    created_topics = created_topics + 1

                elif (
                    subscriber
                    not in cached_topics[topic_generated]["topic"].subscribers
                ):
                    cached_topics[topic_generated]["topic"].subscribers.append(
                        copy.deepcopy(subscriber)
                    )
                    cached_topics[topic_generated]["updated"] = True
                    updated_subscribers = updated_subscribers + 1

    topic_updates = []
    for _, topic_info in cached_topics.items():
        if topic_info["updated"]:
            topic_updates.append(topic_info["topic"])

    db.bulk_update(topic_updates)

    return updated_subscribers, created_topics


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

    All topic handling is done at the Mongo level or scheduled jobs

    Args:
        event: The event to handle
    """

    pass
