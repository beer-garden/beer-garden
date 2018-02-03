import logging
import logging.handlers
import os


class PluginHandler(object):
    """Basic Logging Handler for Plugins"""
    def __init__(self, handlerFactory, plugin_name, log_directory=None, **kw):
        if log_directory is not None:
            kw['filename'] = os.path.join(log_directory, plugin_name + '.log')

        kw['maxBytes'] = 10485760  # 10MB
        kw['backupCount'] = 5
        self._handler = handlerFactory(**kw)

    def __getattr__(self, attr):
        if hasattr(self._handler, attr):
            return getattr(self._handler, attr)
        raise AttributeError(attr)


# Since we are imitating the logging module, we will allow camel case method names
def getPluginLogger(name, formatted=True, log_directory=None):
    """
    Get a Plugin Logger. If formatted is set to true, do no special formatting.
    Otherwise, make the logger log to something semi-pretty

    :param name:
    :param formatted:
    :return:
    """
    log = logging.getLogger(name)
    log.propagate = False
    if len(log.handlers) > 0:
        return log

    if log_directory:
        handler = PluginHandler(logging.handlers.RotatingFileHandler, name, log_directory)
        handler.setLevel(logging.INFO)
        if formatted:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        else:
            formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
    else:
        handler = logging.getLogger().handlers[0]

    log.addHandler(handler)
    return log


def getLogLevels():
    try:
        # Python 2
        return [n for n in getattr(logging, '_levelNames').keys() if isinstance(n, str)]
    except AttributeError:
        # Python 3
        return [n for n in getattr(logging, '_nameToLevel').keys()]
