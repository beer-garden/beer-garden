class ConfigurationError(Exception):
    """Generic configuration error"""

    pass


class PluginValidationError(Exception):
    """Plugin could not be created successfully"""

    pass


class PluginStartupError(Exception):
    """Plugin could not be started"""

    pass


class ShutdownError(Exception):
    """Backend has been shut down"""

    pass
