import logging

import bartender
from bartender.errors import PluginStartupError
from bartender.local_plugins.plugin_runner import LocalPluginRunner
from bg_utils.mongo.models import System


class LocalPluginsManager(object):
    """LocalPluginsManager that is capable of stopping/starting and restarting plugins"""

    def __init__(self, loader, validator, registry, clients):
        self.logger = logging.getLogger(__name__)
        self.loader = loader
        self.validator = validator
        self.registry = registry
        self.clients = clients

    def start_plugin(self, plugin):
        """Start a specific plugin.

        If a plugin cannot Be found (i.e. it was not loaded) then it will not do anything
        If the plugin is already running, it will do nothing.
        If a plugin instance has not started after the PLUGIN_STARTUP_TIMEOUT it will mark that
        instance as stopped

        :param plugin: The plugin to start
        :return: True if any plugin instances successfully started. False if the plugin does
            not exist or all instances failed to start
        """
        self.logger.info("Starting plugin %s", plugin.unique_name)

        if plugin.status in ["RUNNING", "STARTING"]:
            self.logger.info("Plugin %s is already running.", plugin.unique_name)
            return True

        if plugin.status == "INITIALIZING":
            new_plugin = plugin
        elif plugin.status in ["DEAD", "STOPPED"]:
            new_plugin = LocalPluginRunner(
                plugin.entry_point,
                plugin.system,
                plugin.instance_name,
                plugin.path_to_plugin,
                plugin.web_host,
                plugin.web_port,
                plugin.ssl_enabled,
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
            raise PluginStartupError("Plugin in an invalid state (%s)" % plugin.status)

        new_plugin.status = "STARTING"
        new_plugin.start()

        return True

    def stop_plugin(self, plugin):
        """Stops a Plugin

        :param plugin The plugin to stop.
        :return: None
        """
        self.logger.info("Stopping plugin %s", plugin.unique_name)

        # Need to mark the plugin as dead if it doesn't shut down cleanly
        clean_shutdown = True

        try:
            if plugin.status in ["DEAD", "STOPPED", "STOPPING"]:
                self.logger.info("Plugin %s was already stopped", plugin.unique_name)
                return
            elif plugin.status == "UNKNOWN":
                self.logger.warning(
                    "Couldn't determine status of plugin %s, "
                    "still attempting to stop",
                    plugin.unique_name,
                )
            else:
                plugin.status = "STOPPING"

            # Plugin must be marked as stopped before sending shutdown message
            plugin.stop()

            # Send a stop request. This initiates a graceful shutdown on the plugin side.
            self.clients["pika"].stop(
                system=plugin.system.name,
                version=plugin.system.version,
                instance=plugin.instance_name,
            )

            # Now just wait for the plugin thread to die
            self.logger.info("Waiting for plugin %s to stop...", plugin.unique_name)
            plugin.join(bartender.config.plugin.local.timeout.shutdown)

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
            plugin.status = "DEAD"

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
            raise Exception(message)

        path_to_plugin = plugins[0].path_to_plugin

        # Verify the new configuration is valid before we remove the
        # current plugins from the registry
        if not self.validator.validate_plugin(path_to_plugin):
            message = (
                "Could not reload system %s-%s: new configuration is not valid"
                % (system_name, system_version)
            )
            self.logger.warning(message)
            raise Exception(message)

        for plugin in plugins:
            if plugin.status == "RUNNING":
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
        """Attempts to start all plugins in the registry."""
        self.logger.info("Starting all plugins")
        self._start_multiple_plugins(self.registry.get_all_plugins())

    def _start_multiple_plugins(self, plugins_to_start):
        """Starts multiple plugins, respecting required plugin dependencies.

        It will consider requirements of other plugins. If the plugin requires others, then it
        will be skipped until its requirements are loaded.

        Failure is a little tricky.

        :param plugins_to_start: List of plugin names to be started
        :return: None
        """
        start_list = list(plugins_to_start)

        system_names = self._get_all_system_names()
        failed_system_names = self._get_failed_system_names()
        started_plugin_names = self._get_running_system_names()

        while len(start_list) != 0:
            plugin = start_list.pop()
            attempt_to_start = True

            self.logger.debug("Checking plugin %s's requirements.", plugin.unique_name)
            for required_plugin_name in plugin.requirements:
                if required_plugin_name not in system_names:
                    self.logger.warning(
                        "Plugin %s lists system %s as a required system, "
                        "but that system is not available.",
                        plugin.unique_name,
                        required_plugin_name,
                    )
                    self._mark_as_failed(plugin)
                    failed_system_names.append(plugin.system.name)
                    attempt_to_start = False
                    break

                elif required_plugin_name in failed_system_names:
                    self.logger.warning(
                        "Plugin %s lists plugin %s as a required plugin, "
                        "but plugin %s failed to start,"
                        " thus plugin %s cannot start.",
                        plugin.unique_name,
                        required_plugin_name,
                        required_plugin_name,
                        plugin.unique_name,
                    )
                    self._mark_as_failed(plugin)
                    failed_system_names.append(plugin.system.name)
                    attempt_to_start = False
                    break

                elif required_plugin_name not in started_plugin_names:
                    self.logger.debug(
                        "Skipping Starting Plugin %s because its "
                        "requirements have yet to be started.",
                        plugin.unique_name,
                    )
                    start_list.insert(0, plugin)
                    attempt_to_start = False
                    break

            if attempt_to_start:
                if self.start_plugin(plugin):
                    started_plugin_names.append(plugin.system.name)
                else:
                    failed_system_names.append(plugin.system.name)

        self.logger.info("Finished starting plugins.")

    @staticmethod
    def _get_all_system_names():
        return [system.name for system in System.objects()]

    @staticmethod
    def _get_running_system_names():
        running_system_names = []
        for system in System.objects():
            if all([instance.status == "RUNNING" for instance in system.instances]):
                running_system_names.append(system.name)

        return running_system_names

    @staticmethod
    def _get_failed_system_names():
        failed_system_names = []
        for system in System.objects():
            if all([instance.status == "DEAD" for instance in system.instances]):
                failed_system_names.append(system.name)

        return failed_system_names

    @staticmethod
    def _mark_as_failed(plugin):
        system = System.find_unique(plugin.system.name, plugin.system.version)
        for instance in system.instances:
            if instance.name == plugin.instance_name:
                instance.status = "DEAD"
        system.deep_save()

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

        new_plugins = []
        for plugin_path in scanned_plugins_paths.difference(existing_plugin_paths):
            try:
                loaded_plugins = self.loader.load_plugin(plugin_path)

                if not loaded_plugins:
                    raise Exception("Couldn't load plugin at %s" % plugin_path)

                for plugin in loaded_plugins:
                    new_plugins.append(plugin)
            except Exception as ex:
                self.logger.error(
                    "Error while attempting to load plugin at %s", plugin_path
                )
                self.logger.exception(ex)

        self._start_multiple_plugins(new_plugins)

    def pause_plugin(self, unique_name):
        """Pause a plugin. Not Used yet."""
        plugin = self.registry.get_plugin(unique_name)

        if plugin is None:
            self.logger.warning("Plugin %s is not loaded.", unique_name)
            return

        if plugin.status == "RUNNING":
            plugin.status = "PAUSED"

    def unpause_plugin(self, unique_name):
        """Unpause a plugin. Not Used yet."""
        plugin = self.registry.get_plugin(unique_name)

        if plugin is None:
            self.logger.warning("Plugin %s is not loaded.", unique_name)
            return

        if plugin.status == "PAUSED":
            plugin.status = "RUNNING"
