import bartender
from bg_utils.plugin_logging_loader import PluginLoggingLoader

plugin_logging_config = None


def get_plugin_log_config(system_name=None):
    return plugin_logging_config.get_plugin_log_config(system_name=system_name)


def load_plugin_log_config():
    global plugin_logging_config

    plugin_logging_config = PluginLoggingLoader().load(
        filename=bartender.config.plugin.logging.config_file,
        level=bartender.config.plugin.logging.level,
        default_config=bartender.app_logging_config,
    )
