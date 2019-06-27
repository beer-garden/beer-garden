from time import sleep

from bartender.events import publish_event
from bg_utils.mongo.models import System

import logging

import bartender
from brewtils.models import Events

logger = logging.getLogger(__name__)


def reload_system(system_id):
    """Reload a system configuration

    :param system_id: The system id
    :return None
    """
    system = System.objects.get(id=system_id)

    logger.info("Reloading system: %s-%s", system.name, system.version)
    bartender.application.plugin_manager.reload_system(system.name, system.version)


@publish_event(Events.SYSTEM_REMOVED)
def remove_system(system_id):
    """Removes a system from the registry if necessary.

    :param system_id: The system id
    :return:
    """
    system = System.objects.get(id=system_id)

    # Attempt to stop the plugins
    registered = bartender.application.plugin_registry.get_plugins_by_system(
        system.name, system.version
    )

    # Local plugins get stopped by us
    if registered:
        for plugin in registered:
            bartender.application.plugin_manager.stop_plugin(plugin)
            bartender.application.plugin_registry.remove(plugin.unique_name)

    # Remote plugins get a stop request
    else:
        bartender.application.clients["pika"].stop(
            system=system.name, version=system.version
        )
        count = 0
        while (
            any(instance.status != "STOPPED" for instance in system.instances)
            and count < bartender.config.plugin.local.timeout.shutdown
        ):
            sleep(1)
            count += 1
            system.reload()

    system.reload()

    # Now clean up the message queues
    for instance in system.instances:

        # It is possible for the request or admin queue to be none if we are
        # stopping an instance that was not properly started.
        request_queue = instance.queue_info.get("request", {}).get("name")
        admin_queue = instance.queue_info.get("admin", {}).get("name")

        bartender.application.clients["pyrabbit"].destroy_queue(
            request_queue, force_disconnect=(instance.status != "STOPPED")
        )
        bartender.application.clients["pyrabbit"].destroy_queue(
            admin_queue, force_disconnect=(instance.status != "STOPPED")
        )

    # Finally, actually delete the system
    system.deep_delete()


def rescan_system_directory():
    """Scans plugin directory and starts any new Systems"""
    bartender.application.plugin_manager.scan_plugin_path()
