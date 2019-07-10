# import logging
#
# from datetime import timedelta
# from functools import wraps
#
# from pika import BasicProperties
# from pika.adapters.tornado_connection import TornadoConnection
# from six import string_types
# from tornado.concurrent import return_future
# from tornado.gen import coroutine
# from tornado.httpclient import AsyncHTTPClient
# from tornado.ioloop import IOLoop
# from tornado.queues import Queue
#
# import brew_view
# from bg_utils.event_publisher import EventPublisher
# from bg_utils.mongo.parser import MongoParser
# from bg_utils.pika import get_routing_key
# from brewtils.models import Events
# from brewtils.queues import PikaClient
# from brewtils.rest.client import RestClient
#
#
# class BeergardenPublisher(EventPublisher):
#     def __init__(self):
#         self._client = RestClient(
#             brew_view.config.web.public_fqdn,
#             brew_view.config.web.port,
#             ssl_enabled=brew_view.config.web.ssl.enabled,
#             url_prefix=brew_view.config.web.url_prefix,
#         )
#
#     def _event_prepare(self, event, **kwargs):
#
#         if event.name.startswith("REQUEST"):
#             request = kwargs.pop("request", None)
#             if request:
#                 event.metadata["entity_url"] = self._client.request_url + str(
#                     request.id
#                 )
#                 event.payload = {
#                     k: str(getattr(request, k))
#                     for k in [
#                         "id",
#                         "command",
#                         "system",
#                         "system_version",
#                         "instance_name",
#                     ]
#                 }
#
#         elif event.name.startswith("SYSTEM"):
#             system = kwargs.pop("system", None)
#             if system:
#                 event.metadata["entity_url"] = self._client.system_url + str(system.id)
#                 event.payload = {"id": str(system.id)}
#
#         elif event.name.startswith("INSTANCE"):
#             instance = kwargs.pop("instance", None)
#             if instance:
#                 event.metadata["entity_url"] = self._client.instance_url + str(
#                     instance.id
#                 )
#                 event.payload = {"id": str(instance.id)}
#
#         return event
#
#
# class HttpPublisher(EventPublisher):
#     def __init__(self, urls, ssl_context=None):
#         self._client = AsyncHTTPClient(
#             defaults={"ssl_options": ssl_context} if ssl_context else None
#         )
#         self._urls = urls
#
#     def publish(self, message, **kwargs):
#         for url in self._urls:
#             self._client.fetch(
#                 url,
#                 raise_error=False,
#                 method="POST",
#                 headers={"content-type": "application/json"},
#                 body=message,
#             )
#
#
# class RequestPublisher(EventPublisher):
#     def __init__(self, ssl_context=None):
#         self._client = AsyncHTTPClient(
#             defaults={"ssl_options": ssl_context} if ssl_context else None
#         )
#
#     def publish(self, message, **kwargs):
#         for url in kwargs.get("urls", []):
#             self._client.fetch(
#                 url,
#                 raise_error=False,
#                 method="POST",
#                 headers={"content-type": "application/json"},
#                 body=message,
#             )
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
# class WebsocketPublisher(BeergardenPublisher):
#     """Publisher implementation that publishes to a websocket"""
#
#     def __init__(self, socket_class):
#         BeergardenPublisher.__init__(self)
#
#         self._socket = socket_class
#
#     def publish(self, message, **kwargs):
#         self._socket.publish(message)
#
#     def shutdown(self):
#         self._socket.shutdown()
#
#
# class MongoPublisher(BeergardenPublisher):
#     """Publisher implementation that 'publishes' to Mongo"""
#
#     def publish(self, message, **kwargs):
#         message.save()
#
#     def _event_serialize(self, event, **kwargs):
#         return MongoParser.parse_event(
#             MongoParser.serialize_event(event, to_string=False)
#         )
#
#
# class TornadoPikaPublisher(BeergardenPublisher, PikaClient):
#     def __init__(self, **kwargs):
#         self.logger = logging.getLogger(__name__)
#
#         self._shutdown_timeout = timedelta(seconds=kwargs.pop("shutdown_timeout", 5))
#         self._work_queue = Queue()
#         self._connection = None
#         self._channel = None
#
#         self.coroutiner = CoroutineMaker(
#             {"TornadoConnection": "on_open_callback", "channel": "on_open_callback"}
#         )
#
#         # Trying to get super() to work with incompatible signatures is a nightmare
#         BeergardenPublisher.__init__(self)
#         PikaClient.__init__(self, **kwargs)
#
#         IOLoop.current().spawn_callback(self._process)
#
#     def shutdown(self):
#         return self._work_queue.join(timeout=self._shutdown_timeout)
#
#     @coroutine
#     def _open_connection(self):
#         self._connection = yield self.coroutiner.convert(TornadoConnection)(
#             parameters=self._conn_params
#         )
#
#     @coroutine
#     def _open_channel(self):
#         self._channel = yield self.coroutiner.convert(self._connection.channel)()
#
#     @coroutine
#     def _process(self):
#
#         while True:
#             item = yield self._work_queue.get()
#
#             try:
#                 if not self._connection or not self._connection.is_open:
#                     yield self._open_connection()
#                 if not self._channel or not self._channel.is_open:
#                     yield self._open_channel()
#
#                 yield getattr(self._channel, item[0])(**item[1])
#             finally:
#                 self._work_queue.task_done()
#
#     def publish(self, message, **kwargs):
#         """Publish a message.
#
#         :param message: The message to publish
#         :param kwargs: Additional message properties
#         :Keyword Arguments:
#             * *routing_key* --
#               Routing key to use when publishing
#             * *headers* --
#               Headers to be included as part of the message properties
#             * *expiration* --
#               Expiration to be included as part of the message properties
#         :return: None
#         """
#         self._work_queue.put(
#             (
#                 "basic_publish",
#                 {
#                     "exchange": self._exchange,
#                     "routing_key": kwargs["routing_key"],
#                     "body": message,
#                     "properties": BasicProperties(
#                         app_id="beer-garden",
#                         content_type="text/plain",
#                         headers=kwargs.pop("headers", None),
#                         expiration=kwargs.pop("expiration", None),
#                     ),
#                 },
#             )
#         )
#
#     def _event_publish_args(self, event, **kwargs):
#
#         # Main thing we need to do here is figure out the appropriate routing key
#         args = {}
#         if event.metadata and "routing_key" in event.metadata:
#             args["routing_key"] = event.metadata["routing_key"]
#         elif "request" in kwargs:
#             request = kwargs["request"]
#             args["routing_key"] = get_routing_key(
#                 "request", request.system, request.system_version, request.instance_name
#             )
#         else:
#             args["routing_key"] = "beergarden"
#
#         return args
#
#
# class CoroutineMaker(object):
#     """Helper class to wrap functions in Tornado futures
#
#     Tornado has a nice @return_future decorator that converts a callback-based function
#     into a Tornado async one. The issue is that it expects the wrapped function to take
#     a `callback` argument and invoke that argument when execution is completed.
#
#     We need to convert a couple of pika functions in this way. Unfortunately, they're
#     expecting a callback function to be provided with the `on_open_callback` keyword
#     parameter. So we use this class to wrap the functions and mangle the arguments when
#     the function is called to pass the Tornado-provided callback to the function like
#     it's expecting.
#     """
#
#     def __init__(self, config):
#         self._signatures = {}
#
#         for func, param in config.items():
#             if isinstance(param, int):
#                 self._signatures[func] = self._positional_signature(param)
#
#             elif isinstance(param, string_types):
#                 self._signatures[func] = self._keyword_signature(param)
#
#             else:
#                 raise Exception("Bad configuration")
#
#     def convert(self, func):
#         @return_future
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             try:
#                 args, kwargs = self._signatures[func.__name__](args, kwargs)
#             except KeyError:
#                 pass
#             func(*args, **kwargs)
#
#         return wrapper
#
#     @staticmethod
#     def _positional_signature(position):
#         def signature(args, kwargs):
#             args = list(args)
#             args.insert(position, kwargs.pop("callback"))
#             return args, kwargs
#
#         return signature
#
#     @staticmethod
#     def _keyword_signature(keyword):
#         def signature(args, kwargs):
#             kwargs[keyword] = kwargs.pop("callback")
#             return args, kwargs
#
#         return signature
