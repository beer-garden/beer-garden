import copy
import logging
import re
from typing import List

from brewtils.models import Event, Events, Garden, Subscriber

import beer_garden.config as config
from beer_garden.garden import get_gardens, local_garden
from beer_garden.requests import process_request
from beer_garden.topic import get_all_topics

logger = logging.getLogger(__name__)


def handle_event(event: Event):
    if (event.name == Events.REQUEST_TOPIC_PUBLISH.name) or (
        event.garden == config.get("garden.name")
        and event.name == Events.REQUEST_CREATED.name
        and "_publish" in event.payload.metadata
        and event.payload.metadata["_publish"]
    ):
        if event.name == Events.REQUEST_CREATED.name:
            event.metadata["regex_only"] = True
            if "_topic" in event.payload.metadata:
                event.metadata["topic"] = event.payload.metadata["_topic"]
            else:
                event.metadata["topic"] = (
                    f"{event.payload.namespace}.{event.payload.system}.{event.payload.system_version}.{event.payload.instance_name}.{event.payload.comment}"
                )

            if "_propagate" in event.payload.metadata:
                event.metadata["propagate"] = event.payload.metadata["propagate"]

            # Clear values from exisitng request
            event.payload.id = None
            event.payload.namespace = None
            event.payload.system = None
            event.payload.system_version = None
            event.payload.instance_name = None
            event.payload.command = None
            del event.payload.metadata["_publish"]

        subscribers = []

        for topic in get_all_topics():
            # TODO: Down the road, determine if we need to filter by Subscriber Type because
            # someone will do something non standard

            # The entire topic must be included in the findall output for a total match
            if event.metadata["topic"] in re.findall(
                topic.name, event.metadata["topic"]
            ):
                # get a list of subscribers for matching topic
                subscribers.extend(topic.subscribers)

        if subscribers:
            if "propagate" in event.metadata and event.metadata["propagate"]:
                for garden in get_gardens(include_local=False):
                    process_publish_event(garden, event, subscribers)

            process_publish_event(local_garden(), event, subscribers)


def process_publish_event(garden: Garden, event: Event, subscribers: List[Subscriber]):
    # Iterate over commands on Garden to find matching topic
    garden_subscribers = [
        subscriber
        for subscriber in subscribers
        if subscriber.garden is None or subscriber.garden == garden.name
    ]
    if garden_subscribers:
        for system in garden.systems:
            system_subscribers = [
                subscriber
                for subscriber in garden_subscribers
                if (subscriber.system is None or subscriber.system == system.name)
                and (subscriber.version is None or subscriber.version == system.version)
            ]
            if system_subscribers:
                for command in system.commands:
                    command_subscribers = [
                        subscriber
                        for subscriber in system_subscribers
                        if subscriber.command is None
                        or subscriber.command == command.name
                    ]
                    if command_subscribers:
                        for instance in system.instances:
                            if instance.status == "RUNNING":
                                instance_subscribers = [
                                    subscriber
                                    for subscriber in system_subscribers
                                    if subscriber.command is None
                                    or subscriber.command == command.name
                                ]
                                if instance_subscribers:
                                    event_request = copy.deepcopy(event.payload)
                                    event_request.system = system.name
                                    event_request.system_version = system.version
                                    event_request.namespace = system.namespace
                                    event_request.instance_name = instance.name
                                    event_request.command = command.name
                                    event_request.is_event = True

                                    try:
                                        process_request(event_request)
                                    except Exception as ex:
                                        # If an error occurs while trying to process request, log it and keep running
                                        logger.exception(ex)

    if garden.children:
        for child in garden.children:
            process_publish_event(child, event, subscribers)
