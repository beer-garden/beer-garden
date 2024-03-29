import copy
import logging
import re
from typing import List, Optional

from brewtils.models import Event, Events, Garden, Subscriber

import beer_garden.config as config
from beer_garden.garden import get_gardens, local_garden
from beer_garden.requests import process_request
from beer_garden.topic import get_all_topics, subscriber_match

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
            if re.findall(topic.name, event.metadata["topic"]):
                # get a list of subscribers for matching topic
                subscribers.extend(topic.subscribers)

        if "propagate" in event.metadata and event.metadata["propagate"]:
            for garden in get_gardens(include_local=False):
                process_publish_event(garden, event, subscribers)

        process_publish_event(local_garden(), event, subscribers)


def process_publish_event(
    garden: Garden, event: Event, subscribers: Optional[List[Subscriber]] = None
):
    # Iterate over commands on Garden to find matching topic
    regex_only = "regex_only" in event.metadata and event.metadata["regex_only"]
    for system in garden.systems:
        for command in system.commands:
            for instance in system.instances:
                match = (
                    not regex_only
                    and f"{system.namespace}.{system.name}.{system.version}.{instance.name}.{command.name}"
                    == event.metadata["topic"]
                )
                if not match:
                    for topic in command.topics:
                        if topic == event.metadata["topic"] or event.metadata[
                            "topic"
                        ] in re.findall(topic, event.metadata["topic"]):
                            match = True
                            break

                if not match:
                    event_subscriber = Subscriber(
                        garden=garden.name,
                        system=system.name,
                        namespace=system.namespace,
                        version=system.version,
                        instance=instance.name,
                        command=command.name,
                    )
                    if subscribers:
                        for subscriber in subscribers:
                            if subscriber_match(subscriber, event_subscriber):
                                match = True
                                break

                if match:
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
