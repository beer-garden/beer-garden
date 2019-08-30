from bg_utils.event_publisher import EventPublisher
from bg_utils.mongo.parser import MongoParser
from brewtils.models import Events
from brewtils.rest.client import TimeoutAdapter

from requests import Session


# class WebhookPublisher(EventPublisher):
#     def __init__(self, ssl_context=None):
#         self._session = Session()
#
#         # timeout = kwargs.get("client_timeout", None)
#         timeout = -1
#         if timeout == -1:
#             timeout = None
#
#         # Having two is kind of strange to me, but this is what Requests does
#         self._session.mount("https://", TimeoutAdapter(timeout=timeout))
#         self._session.mount("http://", TimeoutAdapter(timeout=timeout))
#         # self._client = AsyncHTTPClient(
#         #     defaults={"ssl_options": ssl_context} if ssl_context else None
#         # )
#
#     def publish(self, message, **kwargs):
#         for url in kwargs.get("urls", []):
#             self._session.post(
#                 url, data=message, headers={"content-type": "application/json"}
#             )
#             # self._client.fetch(
#             #     url,
#             #     raise_error=False,
#             #     method="POST",
#             #     headers={"content-type": "application/json"},
#             #     body=message,
#             # )
#
#     def _event_publish_args(self, event, **kwargs):
#         urls = []
#
#         if event.name.startswith("REQUEST") and "request" in kwargs:
#             if "webhooks" in kwargs["request"].metadata:
#                 webhook_dict = kwargs["request"].metadata["webhooks"]
#
#                 # Always add current event urls
#                 urls += webhook_dict.get(event.name, [])
#
#                 # Additionally do some quick translation for success / failure
#                 # completion events
#                 if event.name == Events.REQUEST_COMPLETED.name:
#                     urls += webhook_dict.get(
#                         "REQUEST_FAILURE" if event.error else "REQUEST_SUCCESS", []
#                     )
#
#         return {"urls": urls} if urls else {}
#
#
# class WebsocketPublisher(EventPublisher):
#     """Publisher implementation that publishes to a websocket"""
#
#     def __init__(self, socket_class):
#         EventPublisher.__init__(self)
#
#         self._socket = socket_class
#
#     def publish(self, message, **kwargs):
#         self._socket.publish(message)
#
#     def shutdown(self):
#         self._socket.shutdown()


class MongoPublisher(EventPublisher):
    """Publisher implementation that 'publishes' to Mongo"""

    def publish(self, message, **kwargs):
        message.save()

    def _event_serialize(self, event, **kwargs):
        return MongoParser.parse_event(
            MongoParser.serialize_event(event, to_string=False)
        )
