import copy
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List

from brewtils.errors import ModelValidationError
from brewtils.models import Event, Events, Garden, Operation, Request, System, Topic

import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.garden import get_garden
from beer_garden.replication import is_primary_replication
from beer_garden.systems import get_systems
from beer_garden.topic import get_topics_regex

logger = logging.getLogger(__name__)


def get_minimum_gardens():
    """Generates a list of minimum fields for evaluation

    Returns:
        list: Reduced fields for Gardens
    """
    gardens = db.query(
        Garden,
        exclude_fields=[
            "receiving_connections",
            "publishing_connections",
            "status",
            "status_info",
            "systems.instances.status_info",
        ],
    )

    for garden in gardens:
        if garden.connection_type == "LOCAL":
            garden.systems = get_systems(
                filter_params={"local": True}, exclude_fields=["instances.status_info"]
            )

    return gardens


def get_systems_regex(topics: List[Topic]) -> List[System]:
    """Find all potential matching Systems to Topic Subscribers

    Args:
        topics: List of topics to search

    Return:
        list: List of potentially matching systms to subscribers
    """

    or_statements = []
    for topic in topics:
        for subscriber in topic.subscribers:
            where_statements = []

            if subscriber.subscriber_type == "DYNAMIC":

                if subscriber.system:
                    where_statements.append({"name": {"$regex": subscriber.system}})

                if subscriber.version:
                    where_statements.append({"version": {"$regex": subscriber.version}})

                if subscriber.namespace:
                    where_statements.append(
                        {"namespace": {"$regex": subscriber.namespace}}
                    )

                if subscriber.instance:
                    where_statements.append(
                        {"instances.name": {"$regex": subscriber.instance}}
                    )

                if subscriber.command:
                    where_statements.append(
                        {"commands.name": {"$regex": subscriber.command}}
                    )
            else:
                where_statements.append({"name": {"$eq": subscriber.system}})
                where_statements.append({"version": {"$eq": subscriber.version}})
                where_statements.append({"namespace": {"$eq": subscriber.namespace}})

            if where_statements:
                and_statement = {"$and": where_statements}

                if and_statement not in or_statements:
                    or_statements.append(and_statement)

    if or_statements:
        raw_query = {"$or": or_statements}
        return db.query(
            System, raw_query=raw_query, exclude_fields=["instances.status_info"]
        )
    else:
        return None


def get_garden_name(system: System) -> str:
    """Determine the Garden name of System

    Args:
        system (System): System to look up reference Garden name

    Returns:
        str: Garden Name
    """
    gardens = db.query(
        Garden, include_fields=["name"], filter_params={"systems__contains": system}
    )
    if gardens and len(gardens) == 1:
        return gardens[0].name
    raise Exception(f"Error finding matching garden for System: {system}")


def determine_target_garden(request: Request, garden: Garden = None) -> str:
    """Determine the Garden name of a request

    Args:
        request (Request): Request to find target System from
        garden (Garden, optional): Garden to search for matching System. Defaults to None.

    Returns:
        str: Garden Name
    """
    if garden is None:
        garden = get_garden(config.get("garden.name"))

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


def handle_event_filter(event):

    if event.name == Events.REQUEST_TOPIC_PUBLISH.name and (
        event.garden == config.get("garden.name")
        or event.metadata.get("_propagate", False)
    ):
        return False

    return True


def handle_event(event: Event):
    # Only the primary replication should handle publish request events
    if (
        config.get("replication.enabled")
        and hasattr(event.payload, "replication_id")
        and not is_primary_replication(event.payload.replication_id)
    ):
        return

    if event.name == Events.REQUEST_TOPIC_PUBLISH.name and (
        event.garden == config.get("garden.name")
        or event.metadata.get("_propagate", False)
    ):

        topics = get_topics_regex(event.metadata["topic"])
        for topic in topics:
            topic.publisher_count += 1

        if topics:

            matching_systems = get_systems_regex(topics)

            if not event.payload.metadata:
                event.payload.metadata = {}

            event.payload.metadata["_topic"] = event.metadata["topic"]

            requests = process_publish_event(matching_systems, event, topics)

            db.bulk_update(topics)

            if requests:
                # This could be done by generating an asyncio loop to handle
                # the requests, but it is an extreme memory hog
                with ThreadPoolExecutor() as executor:
                    executor.map(route_request, requests)


def route_request(create_request):
    import beer_garden.router as router

    try:
        router.route(
            Operation(
                operation_type="REQUEST_CREATE",
                model=create_request,
                model_type="Request",
            )
        )
    except ModelValidationError as ex:
        logger.error(
            (
                "Invalid request for topic "
                f"'{create_request.metadata.get('_topic', 'Missing Topic')}' "
                f"for request {create_request}: {ex}"
            )
        )
    except Exception as ex:
        # If an error occurs while trying to process request, log it and keep running
        logger.exception(ex)


def find_subscribers(subscribers, subscriber_field: str, compare_value):
    """Make sub-list of subscribers based off filtering criteria

    Args:
        subscribers (list[Subscriber]): List of subscribers to filter
        subscriber_field (str): Field on Subscriber object to compare against
        compare_value (str): Field to compare against Subscriber field
    Return:
        list[Subscriber]: Sub list that match against field and compare value
    """
    if subscribers:
        return [
            subscriber
            for subscriber in subscribers
            if (
                getattr(subscriber, subscriber_field) is None
                or len(getattr(subscriber, subscriber_field)) == 0
                or compare_value == getattr(subscriber, subscriber_field, None)
            )
            or (
                subscriber.subscriber_type == "DYNAMIC"
                and compare_value
                in re.findall(getattr(subscriber, subscriber_field), compare_value)
            )
        ]
    return subscribers


def process_publish_event(
    systems: List[System], event: Event, topics: List[Topic]
) -> List[Request]:
    """Create a unique list of Requests based off Systems and Topics

    Args:
        systems (list[System]): A full list of all potential matching systems
        event (Event): The originating Event to build Requests off of
        Topics (list[Topic]): List of Topics with subscribers to push Requests to
    Return:
        list[Request]: List of Requests generated off Subscriber matches
    """
    requests = []
    requests_hash = []

    for topic in topics:

        for system in systems:

            system_name_subscribers = find_subscribers(
                topic.subscribers, "system", system.name
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

            if system.local:
                garden_name = config.get("garden.name")

            else:
                garden_name = get_garden_name(system)

            garden_subscribers = find_subscribers(
                system_version_subscribers, "garden", garden_name
            )

            if not garden_subscribers:
                continue

            for command in system.commands:
                command_subscribers = find_subscribers(
                    garden_subscribers, "command", command.name
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
                        event_request.command_type = command.command_type
                        event_request.has_parent = True
                        event_request.is_event = True

                        request_hash = (
                            f"{garden_name}.{system.namespace}."
                            f"{system.name}.{system.version}."
                            f"{instance.name}.{command.name}"
                        )

                        if request_hash not in requests_hash:
                            requests_hash.append(request_hash)
                            requests.append(event_request)

                        for instance_subscriber in instance_subscribers:
                            instance_subscriber.consumer_count += 1

    return requests
