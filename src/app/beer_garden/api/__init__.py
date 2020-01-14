# -*- coding: utf-8 -*-
import logging

import wrapt

import beer_garden
import beer_garden.commands
import beer_garden.instances
import beer_garden.log
import beer_garden.plugin
import beer_garden.queues
import beer_garden.requests
import beer_garden.scheduler
import beer_garden.systems
import beer_garden.garden


def namespace_router(_wrapped):
    logger = logging.getLogger(__name__)

    def handle_local(namespace):
        # Handle locally if namespace explicitly matches local or if it's empty
        return namespace in (beer_garden.config.get("namespaces.local"), "", None)

    def handle_remote(namespace):
        return namespace in beer_garden.api.remote_ns_names()

    @wrapt.decorator
    def wrapper(wrapped, _, args, kwargs):
        target_ns = args[0]

        if handle_local(target_ns):
            logger.debug(f"Handling {wrapped.__name__} locally")

            return wrapped(*args[1:], **kwargs)

        if handle_remote(target_ns):
            pass

        raise ValueError(f"Unable to find route to namespace '{target_ns}'")

    return wrapper(_wrapped)


def get_version():
    """Gets the current version of the backend"""
    return beer_garden.__version__


def remote_ns_names():
    if not beer_garden.config.get("namespaces.remote"):
        return []

    return [ns.name for ns in beer_garden.config.get("namespaces.remote")]


def get_local_namespace():
    return beer_garden.config.get("namespaces.local")


def get_remote_namespaces():
    return remote_ns_names()


# Requests
get_request = namespace_router(beer_garden.requests.get_request)
get_requests = namespace_router(beer_garden.requests.get_requests)
process_request = namespace_router(beer_garden.requests.process_request)
update_request = namespace_router(beer_garden.requests.update_request)

# Instances / plugins
get_instance = namespace_router(beer_garden.instances.get_instance)
remove_instance = namespace_router(beer_garden.instances.remove_instance)
initialize_instance = namespace_router(beer_garden.plugin.initialize)
start_instance = namespace_router(beer_garden.plugin.start)
stop_instance = namespace_router(beer_garden.plugin.stop)
update_instance_status = namespace_router(beer_garden.plugin.update_status)

# Systems
get_system = namespace_router(beer_garden.systems.get_system)
get_systems = namespace_router(beer_garden.systems.get_systems)
create_system = namespace_router(beer_garden.systems.create_system)
update_system = namespace_router(beer_garden.systems.update_system)
reload_system = namespace_router(beer_garden.systems.reload_system)
remove_system = namespace_router(beer_garden.systems.remove_system)
rescan_system_directory = namespace_router(beer_garden.systems.rescan_system_directory)

# Queues
get_queue_message_count = namespace_router(beer_garden.queues.get_queue_message_count)
get_all_queue_info = namespace_router(beer_garden.queues.get_all_queue_info)
clear_queue = namespace_router(beer_garden.queues.clear_queue)
clear_all_queues = namespace_router(beer_garden.queues.clear_all_queues)

# Scheduler
get_job = namespace_router(beer_garden.scheduler.get_job)
get_jobs = namespace_router(beer_garden.scheduler.get_jobs)
create_job = namespace_router(beer_garden.scheduler.create_job)
pause_job = namespace_router(beer_garden.scheduler.pause_job)
resume_job = namespace_router(beer_garden.scheduler.resume_job)
remove_job = namespace_router(beer_garden.scheduler.remove_job)

# Commands
get_command = namespace_router(beer_garden.commands.get_command)
get_commands = namespace_router(beer_garden.commands.get_commands)

# Log config
get_plugin_log_config = namespace_router(beer_garden.log.get_plugin_log_config)
reload_plugin_log_config = namespace_router(beer_garden.log.reload_plugin_log_config)

# Namespace Config
get_garden = beer_garden.garden.get_garden
update_garden = beer_garden.garden.update_garden
remove_garden = beer_garden.garden.remove_garden
create_garden = beer_garden.garden.create_garden
