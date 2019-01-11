import warnings

from brewtils.plugin import PluginBase


class LocalPlugin(PluginBase):
    pass


class SimpleLocalPlugin(LocalPlugin):
    """Simple Local Plugin for use by Plugin developers"""

    def __init__(self, client, logger=None):
        super(SimpleLocalPlugin, self).__init__(
            client, logger=logger, multithreaded=False
        )
        warnings.warn(
            "Call made to 'SimpleLocalPlugin'. This name will be removed "
            "in version 3.0, please use 'LocalPlugin' instead.",
            DeprecationWarning,
            stacklevel=2,
        )


class MultiThreadedLocalPlugin(LocalPlugin):
    """Multi-threaded Local Plugin for use by Plugin developers"""

    def __init__(self, client, logger=None):
        super(MultiThreadedLocalPlugin, self).__init__(
            client, logger=logger, multithreaded=True
        )
        warnings.warn(
            "Call made to 'MultiThreadedLocalPlugin'. This name will be removed in "
            "version 3.0, please use 'LocalPlugin(multithreaded=True)' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
