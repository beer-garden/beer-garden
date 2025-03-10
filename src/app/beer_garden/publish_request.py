import copy
import logging
import re
from typing import List

from brewtils.models import Event, Events, Garden, Request, Topic

import beer_garden.config as config
from beer_garden.garden import local_garden
from beer_garden.requests import process_request
from beer_garden.topic import (
    get_all_topics,
    increase_consumer_count,
    increase_publish_count,
)

logger = logging.getLogger(__name__)


def determine_target_garden(request: Request, garden: Garden = None) -> str:
    """Determine the Garden name of a request

    Args:
        request (Request): Request to find target System from
        garden (Garden, optional): Garden to search for matching System. Defaults to None.

    Returns:
        str: Garden Name
    """
    if garden is None:
        garden = local_garden(all_systems=True)

    for system in garden.systems:
        if (
            system.namespace == request.namespace
            and system.name == request.system
            and system.version == request.system_version
        ):
            instance_match = False
            for instance in system.instances:
                if instance.name == request.instance_name:
                    instance_match = True
                    break
            if instance_match:
                for command in system.commands:
                    if command.name == request.command:
                        return garden.name

    for child in garden.children:
        garden_name = determine_target_garden(request, garden=child)
        if garden_name:
            return garden_name

    return None


def handle_event(event: Event):
    if (
        event.name == Events.REQUEST_TOPIC_PUBLISH.name
        and (
            event.garden == config.get("garden.name")
            or event.metadata.get("_propagate", False)
        )
    ) or (
        event.name == Events.REQUEST_CREATED.name
        and event.payload.metadata.get("_publish", False)
        and (
            event.garden == config.get("garden.name")
            or event.payload.metadata.get("_propagate", False)
        )
    ):
        if event.name == Events.REQUEST_CREATED.name:

            if "_topic" in event.payload.metadata:
                event.metadata["topic"] = event.payload.metadata["_topic"]
            else:
                # Need to find the source garden for the system
                garden_name = determine_target_garden(event.payload)
                if garden_name:
                    event.metadata["topic"] = (
                        f"{garden_name}.{event.payload.namespace}."
                        f"{event.payload.system}.{event.payload.system_version}."
                        f"{event.payload.instance_name}.{event.payload.command}"
                    )
                else:
                    logger.error(
                        (
                            f"Unable to determine target Garden for system "
                            f"{event.payload.namespace}."
                            f"{event.payload.system}."
                            f"{event.payload.system_version}."
                            f"{event.payload.instance_name}."
                            f"{event.payload.command}"
                        )
                    )
                    return

            # Clear values from existing request
            event.payload.id = None
            event.payload.namespace = None
            event.payload.system = None
            event.payload.system_version = None
            event.payload.instance_name = None
            event.payload.command = None
            del event.payload.metadata["_publish"]

        topics = []

        for topic in get_all_topics():
            # TODO: Down the road, determine if we need to filter by Subscriber Type because
            # someone will do something non standard

            # The entire topic must be included in the findall output for a total match
            if event.metadata["topic"] in re.findall(
                topic.name, event.metadata["topic"]
            ):

                topic = increase_publish_count(topic)
                topics.append(topic)

        if topics:
            process_publish_event(local_garden(), event, topics)


def find_subscribers(subscribers, subscriber_field: str, compare_value):
    if subscribers:
        return [
            subscriber
            for subscriber in subscribers
            if (
                subscriber.subscriber_type in ["GENERATED", "ANNOTATED"]
                and compare_value in getattr(subscriber, subscriber_field, [])
            )
            or (
                subscriber.subscriber_type == "DYNAMIC"
                and (
                    getattr(subscriber, subscriber_field) is None
                    or len(getattr(subscriber, subscriber_field)) == 0
                    or compare_value
                    in re.findall(getattr(subscriber, subscriber_field), compare_value)
                )
            )
        ]
    return subscribers


def process_publish_event(garden: Garden, event: Event, topics: List[Topic]):

    requests = []
    requests_hash = []

    for topic in topics:
        # Iterate over commands on Garden to find matching topic
        garden_subscribers = find_subscribers(topic.subscribers, "garden", garden.name)

        if not garden_subscribers:
            continue

        for system in garden.systems:

            system_name_subscribers = find_subscribers(
                garden_subscribers, "system", system.name
            )

            if not system_name_subscribers:
                continue

            system_namespace_subscribers = find_subscribers(
                system_name_subscribers, "namespace", system.namespace
            )

            if not system_namespace_subscribers:
                continue

            system_version_subscribers = find_subscribers(
                system_namespace_subscribers, "version", system.version
            )

            if not system_version_subscribers:
                continue

            for command in system.commands:
                command_subscribers = find_subscribers(
                    system_name_subscribers, "command", command.name
                )

                if not command_subscribers:
                    continue

                for instance in system.instances:
                    if instance.status == "RUNNING":
                        instance_subscribers = find_subscribers(
                            command_subscribers,
                            "instance",
                            instance.name,
                        )

                        if not instance_subscribers:
                            continue

                        event_request = copy.deepcopy(event.payload)
                        event_request.system = system.name
                        event_request.system_version = system.version
                        event_request.namespace = system.namespace
                        event_request.instance_name = instance.name
                        event_request.command = command.name
                        event_request.is_event = True

                        request_hash = (
                            f"{garden.name}.{system.namespace}."
                            f"{system.name}.{system.version}."
                            f"{instance.name}.{command.name}"
                        )

                        if request_hash not in requests_hash:
                            requests_hash.append(request_hash)
                            requests.append(event_request)

                        for instance_subscriber in instance_subscribers:
                            increase_consumer_count(topic, instance_subscriber)

    if requests:
        for create_request in requests:
            try:
                process_request(create_request)
            except Exception as ex:
                # If an error occurs while trying to process request, log it and keep running
                logger.exception(ex)

    if garden.children:
        for child in garden.children:
            process_publish_event(child, event, topics)
