import logging
from collections import MutableMapping
from datetime import datetime

from six import iteritems

from brewtils.schema_parser import SchemaParser


class EventPublishers(MutableMapping):
    """Class that makes it easy to publish events to one or more Connections"""

    def __init__(self, connections=None):
        self._logger = logging.getLogger(__name__)
        self._connections = connections or {}

        self.metadata_funcs = {}

    def publish_event(self, event, **kwargs):
        """Publish event to all connections

        :param event: The Event to publish
        :param kwargs: Additional arguments to be used when preparing the event
        """
        if not event.timestamp:
            event.timestamp = datetime.utcnow

        for (key, func) in iteritems(self.metadata_funcs):
            event.metadata[key] = func()

        for (name, connection) in iteritems(self._connections):
            try:
                connection.publish_event(event, **kwargs)
            except Exception as ex:
                self._logger.exception(
                    "Exception while publishing event to '%s' connection: %s", name, ex
                )

    def shutdown(self):
        return [c.shutdown() for c in self._connections.values()]

    # Delegate all container operations to _connections
    def __getitem__(self, item):
        return self._connections.__getitem__(item)

    def __setitem__(self, key, value):
        self._connections.__setitem__(key, value)

    def __delitem__(self, key):
        self._connections.__delitem__(key)

    def __iter__(self):
        return self._connections.__iter__()

    def __len__(self):
        return self._connections.__len__()


class EventPublisher(object):
    """Mixin that marks a connection as able to publish event notifications"""

    def publish_event(self, event, **kwargs):
        event = self._event_prepare(event, **kwargs)
        pub_args = self._event_publish_args(event, **kwargs)

        self.publish(self._event_serialize(event, **kwargs), **pub_args)

    def publish(self, message, **kwargs):
        pass

    def shutdown(self):
        pass

    def _event_prepare(self, event, **kwargs):
        """Override to make modifications to the event before publishing"""
        return event

    def _event_serialize(self, event, **kwargs):
        """Override to change how the event is serialized"""
        return SchemaParser.serialize_event(event)

    def _event_publish_args(self, event, **kwargs):
        """Override to supply any additional kwargs to publish_event"""
        return {}
