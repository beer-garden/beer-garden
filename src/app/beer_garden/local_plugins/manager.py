# -*- coding: utf-8 -*-

import logging

from brewtils.models import Instance

import beer_garden.db.api as db
import beer_garden.local_plugins.validator as validator
from beer_garden.errors import PluginStartupError
from beer_garden.instances import stop_instance
from beer_garden.local_plugins.loader import LocalPluginLoader
from beer_garden.local_plugins.plugin_runner import PluginRunner
from beer_garden.local_plugins.registry import LocalPluginRegistry


class LocalPluginsManager(object):
    """Manager that is capable of stopping/starting and restarting plugins"""

    def __init__(self, shutdown_timeout):
        self.logger = logging.getLogger(__name__)
        self.loader = LocalPluginLoader.instance()
        self.registry = LocalPluginRegistry.instance()
        self.shutdown_timeout = shutdown_timeout

    def start_plugin(self, plugin):
        """Start a specific plugin.

        If a plugin cannot be found (i.e. it was not loaded) then it will not do anything
        If the plugin is already running, it will do nothing.
        If a plugin instance has not started after the PLUGIN_STARTUP_TIMEOUT it will
        mark that instance as stopped

        :param plugin: The plugin to start
        :return: True if any plugin instances successfully started. False if the plugin
        does not exist or all instances failed to start
        """
        self.logger.info("Starting plugin %s", plugin.unique_name)

        plugin_instance = db.query_unique(Instance, id=plugin.instance.id)
        plugin_status = plugin_instance.status

        if plugin_status in ["RUNNING", "STARTING"]:
            self.logger.info("Plugin %s is already running.", plugin.unique_name)
            return True

        if plugin_status == "INITIALIZING":
            new_plugin = plugin
        elif plugin_status in ["DEAD", "STOPPED"]:
            new_plugin = PluginRunner(
                plugin.entry_point,
                plugin.system,
                plugin.instance_name,
                plugin.path_to_plugin,
                plugin.web_host,
                plugin.web_port,
                ssl_enabled=plugin.ssl_enabled,
                plugin_args=plugin.plugin_args,
                environment=plugin.environment,
                requirements=plugin.requirements,
                plugin_log_directory=plugin.plugin_log_directory,
                url_prefix=plugin.url_prefix,
                ca_verify=plugin.ca_verify,
                ca_cert=plugin.ca_cert,
                username=plugin.username,
                password=plugin.password,
            )
            self.registry.remove(plugin.unique_name)
            self.registry.register_plugin(new_plugin)
        else:
            raise PluginStartupError("Plugin in an invalid state (%s)" % plugin_status)

        plugin_instance.status = "STARTING"
        db.update(plugin_instance)

        new_plugin.start()

        return True

    def stop_plugin(self, plugin):
        """Stops a Plugin

        :param plugin The plugin to stop.
        :return: None
        """
        self.logger.info("Stopping plugin %s", plugin.unique_name)

        plugin_instance = db.query_unique(Instance, id=plugin.instance.id)
        plugin_status = plugin_instance.status

        # Need to mark the plugin as dead if it doesn't shut down cleanly
        clean_shutdown = True

        try:
            if plugin_status in ["DEAD", "STOPPED", "STOPPING"]:
                self.logger.info("Plugin %s was already stopped", plugin.unique_name)
                return
            elif plugin_status == "UNKNOWN":
                self.logger.warning(
                    "Couldn't determine status of plugin %s, "
                    "still attempting to stop",
                    plugin.unique_name,
                )
            else:
                plugin_instance.status = "STOPPING"
                db.update(plugin_instance)

            # Plugin must be marked as stopped before sending shutdown message
            plugin.stop()

            stop_instance(plugin_instance.id)

            # Now just wait for the plugin thread to die
            self.logger.info("Waiting for plugin %s to stop...", plugin.unique_name)
            plugin.join(self.shutdown_timeout)

        except Exception as ex:
            clean_shutdown = False
            self.logger.error(
                "Plugin %s raised exception while shutting down:", plugin.unique_name
            )
            self.logger.exception(ex)

        finally:
            if plugin.is_alive():
                self.logger.error(
                    "Plugin %s didn't terminate, about to kill", plugin.unique_name
                )
                plugin.kill()
                clean_shutdown = False

        # Local plugins will set their status to STOPPED in their stop handler
        if not clean_shutdown:
            self.logger.warning(
                "Plugin %s did not shutdown cleanly, " "marking as DEAD",
                plugin.unique_name,
            )
            plugin_instance.status = "DEAD"
            db.update(plugin_instance)

    def restart_plugin(self, plugin):
        self.stop_plugin(plugin)
        self.start_plugin(plugin)

    def reload_system(self, system_name, system_version):
        """Reload a specific system

        :param system_name: The name of the system to reload
        :param system_version: The version of the system to reload
        :return: None
        """
        plugins = self.registry.get_plugins_by_system(system_name, system_version)
        if len(plugins) < 1:
            message = "Could not reload system %s-%s: not found in the registry" % (
                system_name,
                system_version,
            )
            self.logger.error(message)
            raise Exception(message)  # TODO - Should not be raising Exception

        path_to_plugin = plugins[0].path_to_plugin

        # Verify the new configuration is valid before we remove the
        # current plugins from the registry
        if not validator.validate_plugin(path_to_plugin):
            message = (
                "Could not reload system %s-%s: new configuration is not valid"
                % (system_name, system_version)
            )
            self.logger.warning(message)
            raise Exception(message)

        for plugin in plugins:
            plugin_instance = db.query_unique(Instance, id=plugin.instance.id)
            plugin_status = plugin_instance.status
            if plugin_status == "RUNNING":
                message = "Could not reload system %s-%s: running instances" % (
                    system_name,
                    system_version,
                )
                self.logger.warning(message)
                raise Exception(message)

        for plugin in plugins:
            self.registry.remove(plugin.unique_name)

        self.loader.load_plugin(path_to_plugin)

    def start_all_plugins(self):
        """Attempts to start all plugins"""
        self.logger.debug("Starting all plugins")

        for plugin in self.registry.get_all_plugins():
            self.start_plugin(plugin)

    def stop_all_plugins(self):
        """Attempt to stop all plugins."""
        self.logger.info("Stopping all plugins")

        for plugin in self.registry.get_all_plugins():
            try:
                self.stop_plugin(plugin)
            except Exception as ex:
                self.logger.error("Error stopping plugin %s", plugin.unique_name)
                self.logger.exception(ex)

    def scan_plugin_path(self):
        """Scans the default plugin directory for new plugins.

        Will also start any new plugins found.

        :return: None
        """
        scanned_plugins_paths = set(self.loader.scan_plugin_path())
        existing_plugin_paths = set(
            [plugin.path_to_plugin for plugin in self.registry.get_all_plugins()]
        )

        for plugin_path in scanned_plugins_paths.difference(existing_plugin_paths):
            try:
                loaded_plugins = self.loader.load_plugin(plugin_path)

                if not loaded_plugins:
                    raise Exception("Couldn't load plugin at %s" % plugin_path)

                for plugin in loaded_plugins:
                    self.start_plugin(plugin)
            except Exception as ex:
                self.logger.error(
                    "Error while attempting to load plugin at %s", plugin_path
                )
                self.logger.exception(ex)
