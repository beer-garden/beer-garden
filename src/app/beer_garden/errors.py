# -*- coding: utf-8 -*-


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


class LoggingLoadingError(Exception):
    """Unable to load Plugin logging configuration"""

    pass


class EndpointRemovedException(Exception):
    """Requested endpoint is no longer valid"""

    def __init__(self, message=None):
        self.message = message


# Routing
class RoutingException(Exception):
    """Base Routing Exception"""

    pass


class UnknownGardenException(RoutingException):
    """Route requested is not valid"""

    pass


class RoutingRequestException(RoutingException):
    """Route requested is not valid"""

    pass


class ForwardException(RoutingException):
    """Error forwarding an Operation"""

    def __init__(self, message=None, operation=None, event_name=None):
        self.message = message
        self.operation = operation
        self.event_name = event_name


# Database
class NotFoundException(Exception):
    """Something wasn't found"""

    pass


class NotUniqueException(Exception):
    """Something wasn't unique"""

    pass
