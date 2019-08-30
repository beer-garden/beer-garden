import beer_garden
from beer_garden.bg_utils.plugin_logging_loader import PluginLoggingLoader

plugin_logging_config = None


def get_plugin_log_config(system_name=None):
    return plugin_logging_config.get_plugin_log_config(system_name=system_name)


def load_plugin_log_config():
    global plugin_logging_config

    plugin_logging_config = PluginLoggingLoader().load(
        filename=beer_garden.config.plugin.logging.config_file,
        level=beer_garden.config.plugin.logging.level,
        default_config=beer_garden.app_logging_config,
    )
