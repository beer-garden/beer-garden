import json

import beer_garden
import beer_garden.commands
import beer_garden.instances
import beer_garden.log
import beer_garden.queues
import beer_garden.requests
import beer_garden.scheduler
import beer_garden.systems


def remote_ns_names():
    if not beer_garden.config.get("namespaces.remote"):
        return []

    return [ns.name for ns in beer_garden.config.get("namespaces.remote")]


def get_local_namespace():
    return beer_garden.config.get("namespaces.local")


def get_remote_namespaces():
    return remote_ns_names()


def get_request(request_id):
    return beer_garden.requests.get_request(request_id)


def get_requests(**kwargs):
    return beer_garden.requests.get_requests(**kwargs)


def process_request(request, wait_timeout):
    """Validates and publishes a Request.

    :param str request: The Request to process
    :raises InvalidRequest: If the Request is invalid in some way
    :return: None
    """
    return beer_garden.requests.process_request(request, wait_timeout)


def update_request(request_id, patch):
    return beer_garden.requests.update_request(request_id, patch)


def get_instance(instance_id):
    return beer_garden.instances.get_instance(instance_id)


def initialize_instance(instance_id):
    """Initializes an instance.

    :param instance_id: The ID of the instance
    :return: QueueInformation object describing message queue for this system
    """
    return beer_garden.instances.initialize_instance(instance_id)


def update_instance(instance_id, patch):
    return beer_garden.instances.update_instance(instance_id, patch)


def start_instance(instance_id):
    """Starts an instance.

    :param instance_id: The ID of the instance
    :return: None
    """
    return beer_garden.instances.start_instance(instance_id)


def stop_instance(instance_id):
    """Stops an instance.

    :param instance_id: The ID of the instance
    :return: None
    """
    return beer_garden.instances.stop_instance(instance_id)


def update_instance_status(instance_id, new_status):
    """Update instance status.

    Args:
        instance_id: The instance ID
        new_status: The new status

    Returns:

    """
    return (beer_garden.instances.update_instance_status(instance_id, new_status),)


def remove_instance(instance_id):
    """Removes an instance.

    :param instance_id: The ID of the instance
    :return: None
    """
    beer_garden.instances.remove_instance(instance_id)


def get_system(system_id):
    return beer_garden.systems.get_system(system_id)


def query_systems(**query_params):
    return beer_garden.systems.query_systems(**query_params)


def create_system(system):
    return beer_garden.systems.create_system(system)


def update_system(system_id, patch):
    return beer_garden.systems.update_system(system_id, patch)


def reload_system(system_id):
    """Reload a system configuration

    :param system_id: The system id
    :return None
    """
    beer_garden.systems.reload_system(system_id)


def remove_system(system_id):
    """Removes a system from the registry if necessary.

    :param system_id: The system id
    :return:
    """
    beer_garden.systems.remove_system(system_id)


def rescan_system_directory():
    """Scans plugin directory and starts any new Systems"""
    beer_garden.systems.rescan_system_directory()


def get_queue_message_count(queue_name):
    """Gets the size of a queue

    :param queue_name: The queue name
    :return: number of messages currently on the queue
    :raises Exception: If queue does not exist
    """
    return beer_garden.queues.get_queue_message_count(queue_name)


def get_all_queue_info():
    return beer_garden.queues.get_all_queue_info()


def clear_queue(queue_name):
    """Clear all Requests in the given queue

    Will iterate through all requests on a queue and mark them as "CANCELED".

    :param queue_name: The queue to clean
    :raises InvalidSystem: If the system_name/instance_name does not match a queue
    """
    beer_garden.queues.clear_queue(queue_name)


def clear_all_queues():
    """Clears all queues that Bartender knows about"""
    beer_garden.queues.clear_all_queues()


def get_job(job_id):
    return beer_garden.scheduler.get_job(job_id)


def get_jobs(filter_params):
    return beer_garden.scheduler.get_jobs(filter_params)


def create_job(job):
    return beer_garden.scheduler.create_job(job)


def pause_job(job_id):
    return beer_garden.scheduler.pause_job(job_id)


def resume_job(job_id):
    return beer_garden.scheduler.resume_job(job_id)


def remove_job(job_id):
    beer_garden.scheduler.remove_job(job_id)


def get_command(command_id):
    return beer_garden.commands.get_command(command_id)


def get_commands():
    return beer_garden.commands.get_commands()


def get_plugin_log_config(system_name):
    return beer_garden.log.get_plugin_log_config(system_name)


def reload_plugin_log_config():
    beer_garden.log.load_plugin_log_config()

    return beer_garden.log.get_plugin_log_config()


def get_version():
    """Gets the current version of the backend"""
    return beer_garden.__version__
