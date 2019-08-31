import logging

from brewtils.stoppable_thread import StoppableThread


class LocalPluginMonitor(StoppableThread):
    """Object to constantly monitor that plugins are alive and working.

    When one is down and out, it will attempt to restart that plugin.
    """

    def __init__(self, plugin_manager, registry):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Local Plugin Monitor"
        self.plugin_manager = plugin_manager
        self.registry = registry

        super(LocalPluginMonitor, self).__init__(
            logger=self.logger, name="LocalPluginMonitor"
        )

    def run(self):
        self.logger.info(self.display_name + " is started")

        while not self.wait(1):
            self.monitor()

        self.logger.info(self.display_name + " is stopped")

    def monitor(self):
        """Make sure plugins stay alive.

        Iterate through all plugins, testing them one at a time.
        If any of them are dead restart them, otherwise just keep chugging along.
        """
        for plugin in self.registry.get_all_plugins():
            if self.stopped():
                break

            if (
                plugin.process
                and plugin.process.poll() is not None
                and not plugin.stopped()
            ):
                if plugin.status == "RUNNING":
                    self.logger.warning(
                        "It looks like plugin %s has " "unexpectedly stopped running.",
                        plugin.unique_name,
                    )
                    self.logger.warning(
                        "If this is happening often, you "
                        "need to talk to the plugin developer."
                    )
                    self.logger.warning("Restarting plugin: %s", plugin.unique_name)

                    plugin.status = "DEAD"
                    self.plugin_manager.restart_plugin(plugin)
                elif plugin.status == "STARTING":
                    self.logger.warning(
                        "It looks like plugin %s has " "failed to start.",
                        plugin.unique_name,
                    )
                    self.logger.warning(
                        "Marking plugin %s as dead.", plugin.unique_name
                    )
                    plugin.status = "DEAD"
