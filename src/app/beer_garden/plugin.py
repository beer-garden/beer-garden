# -*- coding: utf-8 -*-

"""This is the Plugin State Manager"""

import logging
from datetime import datetime

from brewtils.models import Events, Instance, Request, System

import beer_garden
import beer_garden.config
import beer_garden.db.api as db
import beer_garden.queue.api as queue
from beer_garden.events.events_manager import publish_event

logger = logging.getLogger(__name__)


@publish_event(Events.INSTANCE_INITIALIZED)
def initialize(instance_id: str) -> Instance:
    """Initializes an instance.

    Args:
        instance_id: The Instance ID

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)
    system = db.query_unique(System, instances__contains=instance)

    logger.info(
        f"Initializing instance {system.name}[{instance.name}]-{system.version}"
    )

    queue_spec = queue.create(instance)

    instance.status = "INITIALIZING"
    instance.status_info = {"heartbeat": datetime.utcnow()}
    instance.queue_type = queue_spec["queue_type"]
    instance.queue_info = queue_spec["queue_info"]

    instance = db.update(instance)

    start(instance_id)

    return instance


@publish_event(Events.INSTANCE_STARTED)
def start(instance_id: str) -> Instance:
    """Starts an instance.

    Args:
        instance_id: The Instance ID

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)
    system = db.query_unique(System, instances__contains=instance)

    logger.info(f"Starting instance {system.name}[{instance.name}]-{system.version}")

    # Send a request to start to the plugin on the plugin's admin queue
    request = Request.from_template(
        beer_garden.start_request,
        system=system.name,
        system_version=system.version,
        instance_name=instance.name,
    )
    queue.put(request, is_admin=True)

    return instance


@publish_event(Events.INSTANCE_STOPPED)
def stop(instance_id: str) -> Instance:
    """Stops an Instance.

    Args:
        instance_id: The Instance ID

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)
    system = db.query_unique(System, instances__contains=instance)

    logger.info(f"Stopping instance {system.name}[{instance.name}]-{system.version}")

    request = Request.from_template(
        beer_garden.stop_request,
        system=system.name,
        system_version=system.version,
        instance_name=instance.name,
    )
    queue.put(request, is_admin=True)

    return instance


def update_status(instance_id: str, new_status: str) -> Instance:
    """Update an Instance status.

    Will also update the status_info heartbeat.

    Args:
        instance_id: The Instance ID
        new_status: The new status

    Returns:
        The updated Instance
    """
    instance = db.query_unique(Instance, id=instance_id)
    instance.status = new_status
    instance.status_info["heartbeat"] = datetime.utcnow()

    instance = db.update(instance)

    return instance


# class LocalPluginsManager(object):
#     """Manager that is capable of stopping/starting and restarting plugins"""
#
#     def __init__(self, shutdown_timeout):
#         self.logger = logging.getLogger(__name__)
#         self.shutdown_timeout = shutdown_timeout
#
#     def start_plugin(self, plugin):
#         """Start a specific plugin.
#
#         If a plugin cannot be found (i.e. it was not loaded) then it will not do anything
#         If the plugin is already running, it will do nothing.
#         If a plugin instance has not started after the PLUGIN_STARTUP_TIMEOUT it will
#         mark that instance as stopped
#
#         :param plugin: The plugin to start
#         :return: True if any plugin instances successfully started. False if the plugin
#         does not exist or all instances failed to start
#         """
#         self.logger.info("Starting plugin %s", plugin.unique_name)
#
#         plugin.start()
#
#         return True
#
#     def stop_plugin(self, plugin):
#         """Stops a Plugin
#
#         :param plugin The plugin to stop.
#         :return: None
#         """
#         self.logger.info("Stopping plugin %s", plugin.unique_name)
#
#         plugin_instance = db.query_unique(Instance, id=plugin.instance.id)
#         plugin_status = plugin_instance.status
#
#         # Need to mark the plugin as dead if it doesn't shut down cleanly
#         clean_shutdown = True
#
#         try:
#             if plugin_status in ["DEAD", "STOPPED", "STOPPING"]:
#                 self.logger.info("Plugin %s was already stopped", plugin.unique_name)
#                 return
#             elif plugin_status == "UNKNOWN":
#                 self.logger.warning(
#                     "Couldn't determine status of plugin %s, "
#                     "still attempting to stop",
#                     plugin.unique_name,
#                 )
#             else:
#                 plugin_instance.status = "STOPPING"
#                 db.update(plugin_instance)
#
#             # Plugin must be marked as stopped before sending shutdown message
#             plugin.stop()
#
#             stop_instance(plugin_instance.id)
#
#             # Now just wait for the plugin thread to die
#             self.logger.info("Waiting for plugin %s to stop...", plugin.unique_name)
#             plugin.join(self.shutdown_timeout)
#
#         except Exception as ex:
#             clean_shutdown = False
#             self.logger.error(
#                 "Plugin %s raised exception while shutting down:", plugin.unique_name
#             )
#             self.logger.exception(ex)
#
#         finally:
#             if plugin.is_alive():
#                 self.logger.error(
#                     "Plugin %s didn't terminate, about to kill", plugin.unique_name
#                 )
#                 plugin.kill()
#                 clean_shutdown = False
#
#         # Local plugins will set their status to STOPPED in their stop handler
#         if not clean_shutdown:
#             self.logger.warning(
#                 "Plugin %s did not shutdown cleanly, " "marking as DEAD",
#                 plugin.unique_name,
#             )
#             plugin_instance.status = "DEAD"
#             db.update(plugin_instance)
#
#     def restart_plugin(self, plugin):
#         self.stop_plugin(plugin)
#         self.start_plugin(plugin)
#
#     def reload_system(self, system_name, system_version):
#         """Reload a specific system
#
#         :param system_name: The name of the system to reload
#         :param system_version: The version of the system to reload
#         :return: None
#         """
#         plugins = self.registry.get_plugins_by_system(system_name, system_version)
#         if len(plugins) < 1:
#             message = "Could not reload system %s-%s: not found in the registry" % (
#                 system_name,
#                 system_version,
#             )
#             self.logger.error(message)
#             raise Exception(message)  # TODO - Should not be raising Exception
#
#         path_to_plugin = plugins[0].path_to_plugin
#
#         # Verify the new configuration is valid before we remove the
#         # current plugins from the registry
#         if not validator.validate_plugin(path_to_plugin):
#             message = (
#                 "Could not reload system %s-%s: new configuration is not valid"
#                 % (system_name, system_version)
#             )
#             self.logger.warning(message)
#             raise Exception(message)
#
#         for plugin in plugins:
#             plugin_instance = db.query_unique(Instance, id=plugin.instance.id)
#             plugin_status = plugin_instance.status
#             if plugin_status == "RUNNING":
#                 message = "Could not reload system %s-%s: running instances" % (
#                     system_name,
#                     system_version,
#                 )
#                 self.logger.warning(message)
#                 raise Exception(message)
#
#         for plugin in plugins:
#             self.registry.remove(plugin.unique_name)
#
#         self.loader.load_plugin(path_to_plugin)
#
#     def stop_all_plugins(self):
#         """Attempt to stop all plugins."""
#         self.logger.info("Stopping all plugins")
#
#         queue.put(Request.from_template(beer_garden.stop_request), is_admin=True)
#
#     def scan_plugin_path(self):
#         """Scans the default plugin directory for new plugins.
#
#         Will also start any new plugins found.
#
#         :return: None
#         """
#         scanned_plugins_paths = set(self.loader.scan_plugin_path())
#         existing_plugin_paths = set(
#             [plugin.path_to_plugin for plugin in self.registry.get_all_plugins()]
#         )
#
#         for plugin_path in scanned_plugins_paths.difference(existing_plugin_paths):
#             try:
#                 loaded_plugins = self.loader.load_plugin(plugin_path)
#
#                 if not loaded_plugins:
#                     raise Exception("Couldn't load plugin at %s" % plugin_path)
#
#                 for plugin in loaded_plugins:
#                     self.start_plugin(plugin)
#             except Exception as ex:
#                 self.logger.error(
#                     "Error while attempting to load plugin at %s", plugin_path
#                 )
#                 self.logger.exception(ex)
#
#
# class LocalPluginRegistry(object):
#     """Registry that is responsible for keeping track of plugins and their status"""
#
#     _instance = None
#
#     def __init__(self):
#         self._registry = []
#         self.logger = logging.getLogger(__name__)
#
#     @classmethod
#     def instance(cls):
#         if not cls._instance:
#             cls._instance = cls()
#         return cls._instance
#
#     def get_all_plugins(self):
#         """Return a safe copy of all plugins"""
#         return [p for p in self._registry]
#
#     def get_unique_plugin_names(self):
#         """Return a unique set of plugin names"""
#         return set([p.system.name for p in self._registry])
#
#     def get_plugin(self, unique_name):
#         """Returns an actual plugin
#
#         :param unique_name: The unique name of the plugin (name[instance]-version)
#         :return: The plugin
#         """
#         for plugin in self._registry:
#             if plugin.unique_name == unique_name:
#                 return plugin
#
#     def get_plugin_from_instance_id(self, instance_id):
#         instance = db.query_unique(Instance, id=instance_id)
#         system = db.query_unique(System, instances__contains=instance)
#         unique_name = self.get_unique_name(system.name, system.version, instance.name)
#
#         return self.get_plugin(unique_name)
#
#     def get_plugins_by_system(self, system_name, system_version):
#         """Returns a list of plugins with the given system name and version
#
#         :param system_name: The system name
#         :param system_version: The system version
#         :return: List of plugins
#         """
#         return [
#             p
#             for p in self._registry
#             if p.system.name == system_name and p.system.version == system_version
#         ]
#
#     def remove(self, unique_name):
#         """Removes a plugin from the registry
#
#         If a plugin is removed from the registry, it must go through the re-loading
#         process via the PluginLoader. Only used when there is no need for the plugin
#         anymore (system shutdown or plugin is failing to start)
#
#         :param unique_name: The unique name of the plugin, name[instance]-version
#         :return: None
#         """
#         for index, plugin in enumerate(self._registry):
#             if plugin.unique_name == unique_name:
#                 self.logger.info(
#                     "Removing Plugin %s from the registry.", plugin.unique_name
#                 )
#                 self._registry.pop(index)
#                 return
#
#     def register_plugin(self, plugin):
#         """Insert a plugin into the registry
#
#         :param plugin: The plugin to add
#         :return: None
#         """
#         self.logger.debug("Registering plugin %s", plugin.unique_name)
#
#         registered_plugin = self.get_plugin(plugin.unique_name)
#         if registered_plugin is None:
#             self.logger.info(
#                 "Registering Plugin %s in the registry.", plugin.unique_name
#             )
#             self._registry.append(plugin)
#         else:
#             self.logger.info(
#                 "Plugin %s is already in the registry.", registered_plugin.unique_name
#             )
#
#     def plugin_exists(self, plugin_name, plugin_version):
#         """Query if a specific plugin exists in the registry
#
#         :param plugin_name: The plugin name
#         :param plugin_version: The plugin version
#         :return:
#         """
#         for plugin in self._registry:
#             if (
#                 plugin.system.name == plugin_name
#                 and plugin.system.version == plugin_version
#             ):
#                 return True
#         return False
#
#     @staticmethod
#     def get_unique_name(plugin_name, plugin_version, instance_name):
#         return "%s[%s]-%s" % (plugin_name, instance_name, plugin_version)
