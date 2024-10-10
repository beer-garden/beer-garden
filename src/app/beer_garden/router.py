# -*- coding: utf-8 -*-
"""Router Service

The router service is the core of all Entry Points. This provides a single standard that
all entry points can follow in order to interact with Beer Garden Services. Allowing
for the decouple of Entry Points to Services

The router service is responsible for:
* Mapping all Operation Types to Service functions
* Validating the target Garden execution environment
* Forwarding Operations to Downstream Gardens
* Execute any pre-forwarding operations required
* Managing Downstream Garden connections
* Caching `Garden`/`System` information for quick routing decisions
"""

import asyncio
import logging
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from copy import deepcopy
from functools import partial
from typing import Dict, Union

import brewtils.models
from brewtils import EasyClient
from brewtils.models import Connection as BrewtilsConnection
from brewtils.models import Event, Events, Garden, Operation, Request, System
from mongoengine import DoesNotExist
from stomp.exception import ConnectFailedException

import beer_garden
import beer_garden.commands
import beer_garden.config as config
import beer_garden.db.api as db
import beer_garden.files
import beer_garden.garden
import beer_garden.local_plugins.manager
import beer_garden.log
import beer_garden.namespace
import beer_garden.plugin
import beer_garden.queues
import beer_garden.requests
import beer_garden.role
import beer_garden.scheduler
import beer_garden.systems
import beer_garden.topic
import beer_garden.user
from beer_garden.api.stomp.transport import Connection, consolidate_headers, process
from beer_garden.errors import (
    ForwardException,
    RoutingRequestException,
    UnknownGardenException,
)
from beer_garden.events import publish
from beer_garden.garden import get_garden, get_gardens, load_garden_file, update_garden
from beer_garden.metrics import collect_metrics
from beer_garden.requests import complete_request, create_request

logger = logging.getLogger(__name__)

# These are the operations that we will forward to child gardens
routable_operations = [
    "INSTANCE_START",
    "INSTANCE_STOP",
    "REQUEST_CREATE",
    "SYSTEM_DELETE",
    "GARDEN_SYNC",
    "USER_UPSTREAM_SYNC",
]

# Executor used to run REQUEST_CREATE operations in an async context
t_pool = ThreadPoolExecutor()

# Used for actually sending operations to other gardens
garden_lock = threading.RLock()
gardens: Dict[str, Garden] = {}  # garden_name -> garden
stomp_garden_connections: Dict[str, Connection] = {}

# Used for determining WHERE to route an operation
routing_lock = threading.RLock()
system_name_routes: Dict[str, str] = {}
system_id_routes: Dict[str, str] = {}
instance_id_routes: Dict[str, str] = {}

# "Real" async function (async def)
async_functions = {
    "INSTANCE_UPDATE": beer_garden.plugin.update_async,
    "INSTANCE_HEARTBEAT": beer_garden.plugin.heartbeat_async,
}

# Fake async functions that need to be run in an executor when in an async context.
# These are things that require another operation (and so would deadlock without special
# handling) or that would block the event loop for too long.
executor_functions = {
    "REQUEST_CREATE": beer_garden.requests.process_request,
    "INSTANCE_STOP": beer_garden.plugin.stop,
    "SYSTEM_DELETE": beer_garden.systems.purge_system,
    "RUNNER_STOP": beer_garden.local_plugins.manager.stop,
    "RUNNER_DELETE": beer_garden.local_plugins.manager.remove,
    "RUNNER_RELOAD": beer_garden.local_plugins.manager.reload,
}

route_functions = {
    "REQUEST_CREATE": beer_garden.requests.process_request,
    "REQUEST_START": beer_garden.requests.start_request,
    "REQUEST_COMPLETE": beer_garden.requests.complete_request,
    "REQUEST_READ": beer_garden.requests.get_request,
    "REQUEST_READ_ALL": beer_garden.requests.get_requests,
    "REQUEST_DELETE": beer_garden.requests.delete_requests,
    "REQUEST_CANCEL": beer_garden.requests.cancel_requests,
    "REQUEST_UPDATE": beer_garden.requests.update_request,
    "COMMAND_READ": beer_garden.commands.get_command,
    "COMMAND_READ_ALL": beer_garden.commands.get_commands,
    "INSTANCE_READ": beer_garden.systems.get_instance,
    "INSTANCE_DELETE": beer_garden.systems.remove_instance,
    "INSTANCE_UPDATE": beer_garden.plugin.update,
    "INSTANCE_HEARTBEAT": beer_garden.plugin.heartbeat,
    "INSTANCE_INITIALIZE": beer_garden.plugin.initialize,
    "INSTANCE_START": beer_garden.plugin.start,
    "INSTANCE_RESTART": beer_garden.plugin.restart,
    "INSTANCE_STOP": beer_garden.plugin.stop,
    "JOB_CREATE": beer_garden.scheduler.create_job,
    "JOB_CREATE_MULTI": beer_garden.scheduler.create_jobs,
    "JOB_UPDATE": beer_garden.scheduler.update_job,
    "JOB_READ": beer_garden.scheduler.get_job,
    "JOB_READ_ALL": beer_garden.scheduler.get_jobs,
    "JOB_PAUSE": beer_garden.scheduler.pause_job,
    "JOB_RESUME": beer_garden.scheduler.resume_job,
    "JOB_DELETE": beer_garden.scheduler.remove_job,
    "JOB_EXECUTE": beer_garden.scheduler.execute_job,
    "SYSTEM_CREATE": beer_garden.systems.upsert,
    "SYSTEM_READ": beer_garden.systems.get_system,
    "SYSTEM_READ_ALL": beer_garden.systems.get_systems,
    "SYSTEM_UPDATE": beer_garden.systems.update_system,
    "SYSTEM_RELOAD": beer_garden.systems.reload_system,
    "SYSTEM_RESCAN": beer_garden.local_plugins.manager.rescan,  # See RUNNER_RESCAN
    "SYSTEM_DELETE": beer_garden.systems.purge_system,
    "GARDEN_CREATE": beer_garden.garden.create_garden,
    "GARDEN_READ": beer_garden.garden.get_garden,
    "GARDEN_READ_ALL": beer_garden.garden.get_gardens,
    "GARDEN_UPDATE_STATUS": beer_garden.garden.update_garden_status,
    "GARDEN_UPDATE_PUBLISHING_STATUS": beer_garden.garden.update_garden_publishing,
    "GARDEN_UPDATE_RECEIVING_STATUS": beer_garden.garden.update_garden_receiving,
    "GARDEN_DELETE": beer_garden.garden.remove_garden,
    "GARDEN_SYNC": beer_garden.garden.garden_sync,
    "GARDEN_RESCAN": beer_garden.garden.rescan,
    "PLUGIN_LOG_READ": beer_garden.log.get_plugin_log_config,
    "PLUGIN_LOG_READ_LEGACY": beer_garden.log.get_plugin_log_config_legacy,
    "PLUGIN_LOG_RELOAD": beer_garden.log.load_plugin_log_config,
    "QUEUE_READ": beer_garden.queues.get_all_queue_info,
    "QUEUE_DELETE": beer_garden.queues.clear_queue,
    "QUEUE_DELETE_ALL": beer_garden.queues.clear_all_queues,
    "QUEUE_READ_INSTANCE": beer_garden.queues.get_instance_queues,
    "NAMESPACE_READ_ALL": beer_garden.namespace.get_namespaces,
    "FILE_CREATE": beer_garden.files.create_file,
    "FILE_CHUNK": beer_garden.files.create_chunk,
    "FILE_FETCH": beer_garden.files.fetch_file,
    "FILE_DELETE": beer_garden.files.delete_file,
    "FILE_OWNER": beer_garden.files.set_owner,
    "TOPIC_CREATE": beer_garden.topic.create_topic,
    "TOPIC_READ": beer_garden.topic.get_topic,
    "TOPIC_READ_ALL": beer_garden.topic.get_all_topics,
    "TOPIC_DELETE": beer_garden.topic.remove_topic,
    "TOPIC_ADD_SUBSCRIBER": beer_garden.topic.topic_add_subscriber,
    "TOPIC_REMOVE_SUBSCRIBER": beer_garden.topic.topic_remove_subscriber,
    "TOKEN_USER_DELETE": beer_garden.user.revoke_tokens,
    "ROLE_CREATE": beer_garden.role.create_role,
    "ROLE_UPDATE": beer_garden.role.update_role,
    "ROLE_DELETE": beer_garden.role.delete_role,
    "ROLE_READ_ALL": beer_garden.role.get_roles,
    "ROLE_READ": beer_garden.role.get_role,
    "ROLE_RESCAN": beer_garden.role.rescan,
    "RUNNER_READ": beer_garden.local_plugins.manager.runner,
    "RUNNER_READ_ALL": beer_garden.local_plugins.manager.runners,
    "RUNNER_START": beer_garden.local_plugins.manager.start,
    "RUNNER_STOP": beer_garden.local_plugins.manager.stop,
    "RUNNER_DELETE": beer_garden.local_plugins.manager.remove,
    "RUNNER_RELOAD": beer_garden.local_plugins.manager.reload,
    "RUNNER_RESCAN": beer_garden.local_plugins.manager.rescan,
    "USER_READ_ALL": beer_garden.user.get_users,
    "USER_READ": beer_garden.user.get_user,
    "USER_CREATE": beer_garden.user.create_user,
    "USER_UPDATE": beer_garden.user.update_user,
    "USER_DELETE": beer_garden.user.delete_user,
    "USER_RESCAN": beer_garden.user.rescan,
    "USER_SYNC_GARDEN": beer_garden.user.initiate_garden_user_sync,
    "USER_SYNC": beer_garden.user.initiate_user_sync,
    "USER_UPSTREAM_SYNC": beer_garden.user.upstream_users_sync,
    "PUBLISH_EVENT": beer_garden.events.publish,
}

# Filter for fields that should not be published outside of Beer Garden
router_filter = {
    brewtils.models.Garden: beer_garden.garden.filter_router_result,
}


@collect_metrics(transaction_type="router")
def route(operation: Operation):
    """Entry point into the routing subsystem

    Args:
        operation: The operation to route

    Returns:

    """
    operation = _pre_route(operation)

    logger.debug(f"Routing {operation!r}")

    if not operation.operation_type:
        raise RoutingRequestException("Missing operation type")

    if operation.operation_type not in route_functions.keys():
        raise RoutingRequestException(
            f"Unknown operation type '{operation.operation_type}'"
        )

    update_api_heartbeat(operation)

    if invalid_source_check(operation):
        raise RoutingRequestException(
            f"Garden '{operation.source_garden_name}' {operation.source_api} is disabled"
        )

    # Determine which garden the operation is targeting
    operation.target_garden_name = _determine_target(operation)

    # If it's targeted at THIS garden, execute
    if operation.target_garden_name == config.get("garden.name"):
        result = execute_local(operation)
    else:
        result = initiate_forward(operation)

    return filter_result(result)


def filter_result(result: [brewtils.models.BaseModel, list]):
    if result is None:
        return result

    if type(result) is list:
        for item in result:
            filter_result(item)

    if isinstance(result, brewtils.models.Operation):
        filter_result(result.payload)

    if type(result) in router_filter:
        return router_filter[type(result)](result)

    return result


def execute_local(operation: Operation):
    """Execute an operation on the local garden

    Args:
        operation:

    Returns:

    """
    operation = _pre_execute(operation)

    # Default to "normal"
    lookup = route_functions

    loop = None
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        pass

    check_async = True
    if loop and operation.operation_type in async_functions:
        lookup = async_functions
        check_async = False

    if check_async and loop and operation.operation_type in executor_functions:
        response = asyncio.get_event_loop().run_in_executor(
            t_pool,
            partial(
                executor_functions[operation.operation_type],
                *operation.args,
                **operation.kwargs,
            ),
        )
        return response

    return lookup[operation.operation_type](*operation.args, **operation.kwargs)


def update_api_heartbeat(operation: Operation):
    if (
        operation.source_api is not None
        and operation.operation_type == "PUBLISH_EVENT"
        and operation.model.name == Events.GARDEN_SYNC.name
    ):
        if operation.source_garden_name == config.get("garden.name"):

            if operation.model.payload.name != operation.source_garden_name:

                local_garden = get_garden(config.get("garden.name"))

                # Will only support mapping 1 hop away legacy Garden Syncs
                child_garden = False
                for child in local_garden.children:
                    if child.name == operation.model.payload.name:
                        logger.warning(
                            (
                                "Legacy (3.16 or prior) GARDEN_SYNC operation "
                                f"seen for Beer-Garden '{operation.model.payload.name}'"
                            )
                        )
                        operation.source_garden_name = operation.model.payload.name
                        child_garden = True
                        break
                if child_garden:
                    return
            else:
                return

        source_garden = getattr(gardens, operation.source_garden_name, None)
        if operation.model.payload.name == operation.source_garden_name:
            beer_garden.garden.check_garden_receiving_heartbeat(
                operation.source_api,
                garden_name=operation.source_garden_name,
                garden=source_garden,
            )


def invalid_source_check(operation: Operation):
    # Unable to validate source or api
    if (
        operation.source_garden_name is None
        or operation.source_garden_name == config.get("garden.name")
        or operation.source_api is None
    ):
        return False

    # Receiving Connections have not been configured yet
    if operation.source_garden_name in gardens:
        if not gardens[operation.source_garden_name].receiving_connections:
            return False

        for connection in gardens[operation.source_garden_name].receiving_connections:
            if (
                connection.api == operation.source_api
                and connection.status != "DISABLED"
            ):
                return False

    try:
        loaded_garden = beer_garden.garden.get_garden(operation.source_garden_name)
        logger.warning(
            f"Garden {operation.source_garden_name} exists in database and "
            " not in memory routing table, loading into routing table"
        )
    except DoesNotExist:

        loaded_garden = beer_garden.garden.load_garden_file(
            Garden(name=operation.source_garden_name)
        )

        if loaded_garden.status == "NOT_CONFIGURED":
            logger.error(
                f"There is no configuration file for {operation.source_garden_name}, "
                "please validate your children directory for the correct file name"
            )
            return True

        logger.warning(
            f"Loaded {operation.source_garden_name} from config file into in memory"
            " routing table, please manually kick off rescan of directories if this"
            " continues"
        )

    with garden_lock:
        gardens[operation.source_garden_name] = loaded_garden

    # Receiving Connections have not been configured yet
    if not loaded_garden.receiving_connections:
        return False

    for connection in loaded_garden.receiving_connections:
        if connection.api == operation.source_api and connection.status != "DISABLED":
            return False

    return True


def initiate_forward(operation: Operation):
    """Forward an operation to a child garden

    Will:
    - Pre-process the operation
    - Put the operation on the queue for forwarding
    - Return the "correct" response based on operation type

    Args:
        operation:
    """
    operation = _pre_forward(operation)

    # TODO - Check to ensure garden conn_info is not 'local' before forwarding?

    try:
        response = forward(operation)
    except RoutingRequestException:
        # TODO - Special case for dealing with removing downstream systems
        if operation.operation_type == "SYSTEM_DELETE" and operation.kwargs["force"]:
            return beer_garden.systems.remove_system(system=operation.model)

        raise

    # If this is a request create return locally created Request
    if operation.operation_type == "REQUEST_CREATE":
        return operation.model

    return response


def determine_route_garden(target_garden_name):
    target_garden = gardens.get(target_garden_name)

    if not target_garden:
        target_garden = get_garden(target_garden_name)

    routable = False
    for connection in target_garden.publishing_connections:
        if connection.status not in [
            "DISABLED",
            "NOT_CONFIGURED",
            "MISSING_CONFIGURATION",
        ]:
            routable = True
            break

    if not routable:
        raise RoutingRequestException(
            "Attempted to forward operation to garden "
            f"'{target_garden_name}' but the connection was not enabled. "
            "This probably means that the connection to the child garden has not "
            "been configured or the connection is DISABLED"
        )

    if target_garden.has_parent and target_garden.parent != config.get("garden.name"):
        return determine_route_garden(target_garden.parent)

    return target_garden


def forward(operation: Operation):
    """Forward the operation to a child garden

    Intended to be called in the context of an executor or processor.

    Args:
        operation: The operation to forward

    Returns:
        The result of the specific forward transport function used

    Raises:
        RoutingRequestException: Could not determine a route to child
        UnknownGardenException: The specified target garden is unknown
    """
    target_garden = gardens.get(operation.target_garden_name)

    if not target_garden:
        target_garden = get_garden(operation.target_garden_name)

    route_garden = determine_route_garden(operation.target_garden_name)
    try:
        if not target_garden:
            raise UnknownGardenException(
                f"Unknown child garden {operation.target_garden_name}"
            )

        operation_forwarded = False

        exceptions = []
        for connection in route_garden.publishing_connections:
            if connection.status not in [
                "DISABLED",
                "NOT_CONFIGURED",
                "MISSING_CONFIGURATION",
            ]:
                try:
                    if connection.api == "HTTP":
                        _forward_http(operation, route_garden)
                        operation_forwarded = True
                    elif connection.api == "STOMP":
                        _forward_stomp(operation, route_garden)
                        operation_forwarded = True
                except ForwardException as ex:
                    exceptions.append(ex)

        # Throw one of the forwarding exceptions
        for ex in exceptions:
            raise ex
        if not operation_forwarded:
            raise RoutingRequestException(
                "Attempted to forward operation to garden "
                f"'{operation.target_garden_name}' but the connection was not enabled. "
                "This probably means that the connection to the child garden has not "
                "been configured or the connection is DISABLED"
            )

    except ForwardException as ex:
        error_message = str(ex)
        operation = ex.operation

        if operation.operation_type == "REQUEST_CREATE":
            complete_request(
                operation.model.id,
                status="ERROR",
                output=error_message,
                error_class=ex.event_name,
            )

        # Publish an event
        publish(
            Event(
                name=ex.event_name,
                payload_type="Operation",
                payload=operation,
                error_message=error_message,
            )
        )

        raise


def setup_routing():
    """Initialize the routing subsystem

    This will load the cached child garden definitions and use them to populate the
    two dictionaries that matter, garden_lookup and garden_connections.

    It will then query the database for all local systems and add those to the
    dictionaries as well.
    """
    for system in db.query(System, filter_params={"local": True}):
        add_routing_system(system)

    # Don't add the local garden
    for garden in get_gardens(include_local=False):
        if garden.name != config.get("garden.name") and (
            (garden.has_parent and garden.parent == config.get("garden.name"))
            or not garden.has_parent
        ):
            for system in garden.systems:
                add_routing_system(system=system, garden_name=garden.name)

            if (
                garden.connection_type is not None
                and garden.connection_type.casefold() != "local"
            ):
                with garden_lock:
                    gardens[garden.name] = load_garden_file(garden)
                    for connection in gardens[garden.name].publishing_connections:
                        if (
                            connection.api.upper() == "STOMP"
                            and connection.status != "DISABLED"
                        ):
                            if garden.name not in stomp_garden_connections:
                                stomp_garden_connections[garden.name] = (
                                    create_stomp_connection(connection)
                                )

            else:
                logger.warning(f"Garden with invalid connection info: {garden!r}")


def add_routing_system(system=None, garden_name=None):
    """Update the gardens used for routing

    NOTE: THIS NEEDS TO BE ABLE TO BE CALLED MULTIPLE TIMES FOR THE SAME SYSTEM!

    This will be called twice in the HTTP entry point when systems are added, so make
    sure this can handle that without breaking.

    """
    # Default to local garden name
    garden_name = garden_name or config.get("garden.name")

    with routing_lock:
        logger.debug(f"{garden_name}: Adding system {system} ({system.id})")

        system_name_routes[str(system)] = garden_name
        system_id_routes[system.id] = garden_name

        for instance in system.instances:
            logger.debug(f"{garden_name}: Adding {system} instance ({instance.id})")
            instance_id_routes[instance.id] = garden_name


def remove_routing_system(system=None):
    """Update the gardens used for routing"""
    with routing_lock:
        if str(system) in system_name_routes:
            logger.debug(f"Removing system {system}")
            del system_name_routes[str(system)]

        if system.id in system_id_routes:
            logger.debug(f"Removing system {system.id}")
            del system_id_routes[system.id]

        for instance in system.instances:
            if instance.id in instance_id_routes:
                logger.debug(f"Removing {system} instance ({instance.id})")
                del instance_id_routes[instance.id]


def remove_routing_garden(garden_name=None):
    """Remove all routing to a given garden"""
    global system_name_routes, system_id_routes, instance_id_routes
    with routing_lock:
        system_name_routes = {
            k: v for k, v in system_name_routes.items() if v != garden_name
        }
        system_id_routes = {
            k: v for k, v in system_id_routes.items() if v != garden_name
        }
        instance_id_routes = {
            k: v for k, v in instance_id_routes.items() if v != garden_name
        }


def add_routing_garden(garden: Garden, routing_garden: str):
    if garden.systems:
        for system in garden.systems:
            add_routing_system(system=system, garden_name=routing_garden)

    if garden.children:
        for child in garden.children:
            add_routing_garden(child, routing_garden)


def handle_event(event):
    """Handle events"""
    if event.name in (Events.SYSTEM_CREATED.name, Events.SYSTEM_UPDATED.name):
        add_routing_system(system=event.payload, garden_name=event.garden)
    elif event.name == Events.SYSTEM_REMOVED.name:
        remove_routing_system(system=event.payload)

    # Here we want to handle sync events from immediate children only
    if (
        not event.error
        and (event.name == Events.GARDEN_SYNC.name)
        and (event.garden != config.get("garden.name"))
        and (event.garden == event.payload.name)
    ):
        with routing_lock:
            # First remove all current routes to this garden
            remove_routing_garden(garden_name=event.garden)

            # Then add routes to the new systems
            add_routing_garden(event.payload, event.payload.name)

    # This is a little unintuitive. We want to let the garden module deal with handling
    # any downstream garden changes since handling those changes is nontrivial.
    # It's *those* events we want to act on here, not the "raw" downstream ones.
    # This is also why we only handle GARDEN_UPDATED and not STARTED or STOPPED
    if event.garden == config.get("garden.name") and not event.error:
        if event.name == Events.GARDEN_CONFIGURED.name:
            if event.payload.name != config.get("garden.name") and (
                (
                    event.payload.has_parent
                    and event.payload.parent == config.get("garden.name")
                )
                or not event.payload.has_parent
            ):
                gardens[event.payload.name] = event.payload

                stomp_found = False
                for connection in event.payload.publishing_connections:
                    if connection.api.upper() == "STOMP":
                        stomp_found = True
                        if (
                            event.payload.name not in stomp_garden_connections
                            and connection.status == "PUBLISHING"
                        ):
                            stomp_garden_connections[event.payload.name] = (
                                create_stomp_connection(connection)
                            )

                        elif connection.status == "DISABLED":
                            stomp_garden_connections[event.payload.name].disconnect()

            if not stomp_found and event.payload.name not in stomp_garden_connections:
                stomp_garden_connections[event.payload.name].disconnect()
                del stomp_garden_connections[event.payload.name]

        elif event.name == Events.GARDEN_REMOVED.name:
            try:
                del gardens[event.payload.name]
                if event.payload.name in stomp_garden_connections:
                    stomp_garden_connections[event.payload.name].disconnect()
                    del stomp_garden_connections[event.payload.name]
            except KeyError:
                pass
        elif event.name == Events.GARDEN_UPDATED.name:
            gardens[event.payload.name] = event.payload


def _operation_conversion(operation: Operation) -> Operation:
    # Use if the targeted function creates a Request object that
    # needs to be routed to any Garden

    # Instance Logs is expected back a Request object,
    # this converts the class so it can be routed
    if operation.operation_type == "INSTANCE_LOGS":
        return beer_garden.plugin.read_logs_operation(operation)
    return operation


def _pre_route(operation: Operation) -> Operation:
    """Called before any routing logic is applied"""
    # Determine if the operation needs to be converted first
    operation = _operation_conversion(operation)
    # If no source garden is defined set it to the local garden
    if operation.source_garden_name is None:
        operation.source_garden_name = config.get("garden.name")

    if operation.operation_type == "REQUEST_CREATE":
        if operation.model.namespace is None:
            operation.model.namespace = config.get("garden.name")

    return operation


def _pre_forward(operation: Operation) -> Operation:
    """Called before forwarding an operation"""

    # Validate that the operation can be forwarded
    if operation.operation_type not in routable_operations:
        raise RoutingRequestException(
            f"Operation type '{operation.operation_type}' can not be forwarded"
        )

    operation.source_garden_name = None

    if operation.operation_type == "REQUEST_CREATE":
        # Save the request so it'll have an ID and we'll have something to update
        local_request = create_request(operation.model)

        operation.model.id = local_request.id

        beer_garden.files.forward_file(operation)

        # Clear parent before forwarding so the child doesn't freak out about an
        # unknown request
        operation.model.parent = None
        operation.model.has_parent = False
        operation.model.source_garden = None
        operation.model.target_garden = None
        operation.model.metadata = {}

        # Map requester to username on target garden
        if operation.model.requester:
            user_default_user = True
            requester = beer_garden.user.get_user(operation.model.requester)
            for alias_user_map in requester.user_alias_mapping:
                if alias_user_map.target_garden == operation.target_garden_name:
                    operation.model.requester = alias_user_map.username
                    user_default_user = False
                    break

            if user_default_user:
                operation.model.requester = get_garden(
                    operation.target_garden_name
                ).default_user

        # Pull out and store the wait event, if it exists
        wait_event = operation.kwargs.pop("wait_event", None)
        if wait_event:
            beer_garden.requests.request_map[operation.model.id] = wait_event

    return operation


def _pre_execute(operation: Operation) -> Operation:
    """Called before executing an operation"""
    # If there's a model present, shove it in the front
    if operation.model:
        operation.args.insert(0, operation.model)

    return operation


def _determine_target(operation: Operation) -> str:
    """Determine the garden the operation is targeting

    Note that while the operation can already have a target garden field this will only
    be used as a fallback if a better target can't be calculated.

    See https://github.com/beer-garden/beer-garden/issues/1076
    """

    target_garden = _target_from_type(operation)

    if not target_garden:
        if not operation.target_garden_name:
            raise UnknownGardenException(
                f"Could not determine the target garden for routing {operation!r}"
            )

        logger.warning(
            "Couldn't determine a target garden but the operation had one, using "
            f"{operation.target_garden_name}"
        )
        return operation.target_garden_name

    return target_garden


def _target_from_type(operation: Operation) -> str:
    """Determine the target garden based on the operation type"""
    # Certain operations are ASSUMED to be targeted at the local garden
    if (
        "READ" in operation.operation_type
        or "JOB" in operation.operation_type
        or "FILE" in operation.operation_type
        or "TOKEN" in operation.operation_type
        or operation.operation_type
        in (
            "PLUGIN_LOG_RELOAD",
            "SYSTEM_CREATE",
            "SYSTEM_RESCAN",
        )
        or "PUBLISH_EVENT" in operation.operation_type
        or "RUNNER" in operation.operation_type
        or "TOPIC" in operation.operation_type
        or "ROLE" in operation.operation_type
        or operation.operation_type
        in (
            "PLUGIN_LOG_RELOAD",
            "QUEUE_DELETE_ALL",
            "SYSTEM_CREATE",
            "REQUEST_DELETE",
            "REQUEST_CANCEL",
        )
    ):
        return config.get("garden.name")

    # Otherwise, each operation needs to be "parsed"
    if operation.operation_type in ("SYSTEM_RELOAD", "SYSTEM_UPDATE"):
        return _system_id_lookup(operation.args[0])

    if operation.operation_type == "SYSTEM_DELETE":
        # Force deletes get routed to local garden
        if operation.kwargs.get("force"):
            return config.get("garden.name")

        return _system_id_lookup(operation.args[0])

    if "INSTANCE" in operation.operation_type:
        if "system_id" in operation.kwargs and "instance_name" in operation.kwargs:
            return _system_id_lookup(operation.kwargs["system_id"])
        else:
            return _instance_id_lookup(operation.args[0])

    if operation.operation_type in ["REQUEST_CREATE"]:
        operation.model = beer_garden.requests.determine_latest_system_version(
            operation.model
        )
        target_system = System(
            namespace=operation.model.namespace,
            name=operation.model.system,
            version=operation.model.system_version,
        )
        return _system_name_lookup(target_system)

    if operation.operation_type in ["REQUEST_UPDATE"]:
        return config.get("garden.name")

    if operation.operation_type.startswith("REQUEST"):
        request = db.query_unique(Request, id=operation.args[0])
        operation.kwargs["request"] = request

        return config.get("garden.name")

    if "GARDEN" in operation.operation_type:
        if operation.operation_type == "GARDEN_SYNC":
            sync_target = operation.kwargs.get("sync_target")
            if sync_target:
                return sync_target

        return config.get("garden.name")

    if operation.operation_type == "QUEUE_DELETE":
        # Need to deconstruct the queue name
        parts = operation.args[0].split(".")
        version = parts[2].replace("-", ".")

        return _system_name_lookup(
            System(namespace=parts[0], name=parts[1], version=version)
        )

    if "USER" in operation.operation_type:
        if operation.target_garden_name:
            return operation.target_garden_name
        return config.get("garden.name")

    raise Exception(f"Bad operation type {operation.operation_type}")


def _system_name_lookup(system: Union[str, System]) -> str:
    with routing_lock:
        route = system_name_routes.get(str(system))

    if route:
        return route
    else:
        # If we don't know about the route, attempt to find it and update the routing table
        systems = beer_garden.systems.get_systems(
            namespace=system.namespace,
            name=system.name,
            version=system.version,
        )
        if len(systems) == 1:
            for garden in get_gardens():
                for system in garden.systems:
                    if systems[0].id == system.id:
                        with routing_lock:
                            # Then add routes to systems
                            add_routing_system(system=system, garden_name=garden.name)
                        logger.error(
                            "Router mapping is out of sync, you should consider re-syncing"
                        )
                        return garden.name

    return None


def _system_id_lookup(system_id: str) -> str:
    with routing_lock:
        return system_id_routes.get(system_id)


def _instance_id_lookup(instance_id: str) -> str:
    with routing_lock:
        return instance_id_routes.get(instance_id)


# TRANSPORT TYPE STUFF
# This should be moved out of this module
def create_stomp_connection(connection: BrewtilsConnection) -> Connection:
    """Create a stomp connection wrapper for a garden

    Constructs a stomp connection wrapper from the garden's stomp connection parameters.

    Will ignore subscribe_destination as the router shouldn't be subscribing to
    anything.

    Args:
        garden: The garden specifying

    Returns:
        The created connection wrapper

    """

    connection_params = connection.config
    connection_params = deepcopy(connection_params)
    connection_params["subscribe_destination"] = None

    return Connection(**connection_params)


def _forward_stomp(operation: Operation, target_garden: Garden) -> None:
    for connection in target_garden.publishing_connections:
        if connection.api == "STOMP" and connection.status not in [
            "DISABLED",
            "CONFIGURATION_ERROR",
        ]:
            try:
                conn = stomp_garden_connections[target_garden.name]

                if not conn.is_connected() and not conn.connect():
                    connection.status = "UNREACHABLE"
                    update_garden(target_garden)
                    raise ConnectFailedException()

                header_list = connection.config.get("headers", {})
                conn_headers = {}
                for item in header_list:
                    if "key" in item and "value" in item:
                        conn_headers[item["key"]] = item["value"]

                body, model_headers = process(operation)
                headers = consolidate_headers(model_headers, conn_headers)

                conn.send(body=body, headers=headers)
            except Exception as ex:
                connection.status = "ERROR"
                update_garden(target_garden)
                raise ForwardException(
                    message=(
                        "Failed to forward operation to garden "
                        f"'{operation.target_garden_name}' via STOMP."
                    ),
                    operation=operation,
                    event_name=Events.GARDEN_UNREACHABLE.name,
                ) from ex

            if connection.status != "PUBLISHING":
                connection.status = "PUBLISHING"
                update_garden(target_garden)


def _forward_http(operation: Operation, target_garden: Garden) -> None:
    """Actually forward an operation using HTTP"""

    for connection in target_garden.publishing_connections:
        if connection.api == "HTTP" and connection.status not in [
            "DISABLED",
            "CONFIGURATION_ERROR",
        ]:
            easy_client = EasyClient(
                bg_host=connection.config.get("host"),
                bg_port=connection.config.get("port"),
                ssl_enabled=connection.config.get("ssl"),
                bg_url_prefix=connection.config.get("url_prefix", "/"),
                ca_cert=connection.config.get("ca_cert"),
                ca_verify=connection.config.get("ca_verify"),
                client_cert=connection.config.get("client_cert"),
                username=connection.config.get("username"),
                password=connection.config.get("password"),
            )

            try:
                response = easy_client.forward(operation)
                response.raise_for_status()
            except Exception as e:
                connection.status = "UNREACHABLE"
                update_garden(target_garden)
                raise ForwardException(
                    message=f"Error forwarding to garden '{operation.target_garden_name}': {e}",
                    operation=operation,
                    event_name=Events.GARDEN_ERROR.name,
                ) from e

            if connection.status != "PUBLISHING":
                connection.status = "PUBLISHING"
                update_garden(target_garden)
