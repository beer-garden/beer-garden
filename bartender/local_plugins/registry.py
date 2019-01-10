import logging


class LocalPluginRegistry(object):
    """Plugin Registry that is responsible for keeping track of plugins and their status"""

    def __init__(self):
        self._registry = []
        self.logger = logging.getLogger(__name__)

    def get_all_plugins(self):
        """Return a safe copy of all plugins"""
        return [p for p in self._registry]

    def get_unique_plugin_names(self):
        """Return a unique set of plugin names"""
        return set([p.system.name for p in self._registry])

    def get_plugin(self, unique_name):
        """Returns an actual plugin

        :param unique_name: The unique name of the plugin, in the form of name[instance]-version
        :return: The plugin
        """
        for plugin in self._registry:
            if plugin.unique_name == unique_name:
                return plugin

    def get_plugins_by_system(self, system_name, system_version):
        """Returns a list of plugins with the given system name and version

        :param system_name: The system name
        :param system_version: The system version
        :return: List of plugins
        """
        return [
            p
            for p in self._registry
            if p.system.name == system_name and p.system.version == system_version
        ]

    def remove(self, unique_name):
        """Removes a plugin from the registry

        If a plugin is removed from the registry, it must go through the re-loading
        process via the PluginLoader. Only used when there is no need for the plugin
        anymore (system shutdown or plugin is failing to start)

        :param unique_name: The unique name of the plugin, in the form of name[instance]-version
        :return: None
        """
        for index, plugin in enumerate(self._registry):
            if plugin.unique_name == unique_name:
                self.logger.info(
                    "Removing Plugin %s from the registry.", plugin.unique_name
                )
                self._registry.pop(index)
                return

    def register_plugin(self, plugin):
        """Insert a plugin into the registry

        :param plugin: The plugin to add
        :return: None
        """
        self.logger.debug("Registering plugin %s", plugin.unique_name)

        registered_plugin = self.get_plugin(plugin.unique_name)
        if registered_plugin is None:
            self.logger.info(
                "Registering Plugin %s in the registry.", plugin.unique_name
            )
            self._registry.append(plugin)
        else:
            self.logger.info(
                "Plugin %s is already in the registry.", registered_plugin.unique_name
            )

    def plugin_exists(self, plugin_name, plugin_version):
        """Query if a specific plugin exists in the registry

        :param plugin_name: The plugin name
        :param plugin_version: The plugin version
        :return:
        """
        for plugin in self._registry:
            if (
                plugin.system.name == plugin_name
                and plugin.system.version == plugin_version
            ):
                return True
        return False

    @staticmethod
    def get_unique_name(plugin_name, plugin_version, instance_name):
        return "%s[%s]-%s" % (plugin_name, instance_name, plugin_version)
