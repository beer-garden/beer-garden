import logging
import logging.handlers
import os
import sys


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
def getPluginLogger(name, formatted=True, log_directory=None, log_name=None):
    """
    Get a Plugin Logger. If formatted is set to true, do no special formatting.
    Otherwise, make the logger log to something semi-pretty

    Args:
        name (str): The name of the logger to create
        formatted (str / bool): The formatting to apply to the logger
            ``True``: Apply normal plugin formatting
            ``False``: Add no additional formatting, log message as-is
            ``'timestamp'``: Add timestamp to beginning of log message
        log_directory (str, optional): Directory that will hold the log file
            If not given a logger for STDOUT will be constructed
        log_name (str, optional): The name of the log file
            * If ``log_directory`` is not provided this is not used
            * If not provided the ``name`` value will be used

     Returns:
        The configured logger instance
    """
    log = logging.getLogger(name)
    log.propagate = False
    if len(log.handlers) > 0:
        return log

    if log_directory:
        handler = PluginHandler(logging.handlers.RotatingFileHandler,
                                log_name or name, log_directory)
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    if not formatted:
        format_string = '%(message)s'
    elif formatted == 'timestamp':
        format_string = '%(asctime)s - %(message)s'
    else:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(format_string))

    log.addHandler(handler)
    return log


def getLogLevels():
    try:
        # Python 2
        return [n for n in getattr(logging, '_levelNames').keys() if isinstance(n, str)]
    except AttributeError:
        # Python 3
        return [n for n in getattr(logging, '_nameToLevel').keys()]
