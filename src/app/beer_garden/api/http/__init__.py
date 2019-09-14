import logging
import os
import ssl

from apispec import APISpec
from brewtils.rest import normalize_url_prefix
from brewtils.schemas import (
    ParameterSchema,
    CommandSchema,
    InstanceSchema,
    SystemSchema,
    RequestSchema,
    PatchSchema,
    LoggingConfigSchema,
    EventSchema,
    QueueSchema,
    PrincipalSchema,
    RoleSchema,
    RefreshTokenSchema,
    JobSchema,
    DateTriggerSchema,
    IntervalTriggerSchema,
    CronTriggerSchema,
)
from prometheus_client.exposition import start_http_server
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler, RedirectHandler
from urllib3.util.url import Url

import beer_garden.bg_utils
from beer_garden.api.http.authorization import anonymous_principal as load_anonymous

io_loop = None
server = None
tornado_app = None
public_url = None
logger = None
event_publishers = None
api_spec = None
notification_meta = None
anonymous_principal = None
client_ssl = None


def run():
    global logger
    logger = logging.getLogger(__name__)

    _setup_application()

    # Schedule things to happen after the ioloop comes up
    io_loop.add_callback(beer_garden.api.http.startup)

    logger.info("Starting IO loop")

    io_loop.start()

    logger.info("Application is shut down. Goodbye!")


def stop():
    logger.info("Received a shutdown request.")
    # TODO - Should this be 'from_signal'?
    io_loop.add_callback_from_signal(beer_garden.api.http.shutdown)


async def startup():
    """Do startup things.

    This is the first thing called from within the ioloop context.
    """
    global anonymous_principal

    # Need to wait until after mongo connection established to load
    anonymous_principal = load_anonymous()

    metrics_config = beer_garden.config.get("metrics")
    if metrics_config.prometheus.enabled:
        logger.info(
            f"Starting metrics server on "
            f"{metrics_config.prometheus.host}:{metrics_config.prometheus.port}"
        )
        start_http_server(
            metrics_config.prometheus.port, addr=metrics_config.prometheus.host
        )

    web_config = beer_garden.config.get("web")
    logger.info(f"Starting HTTP server on {web_config.host}:{web_config.port}")
    server.listen(web_config.port, web_config.host)

    beer_garden.api.http.logger.info("Application is started. Hello!")


async def shutdown():
    """Do shutdown things

    This still operates within the ioloop, so stopping it should be the last
    thing done.

    Because things in startup aren't guaranteed to have been run we need to be
    careful about checking to make sure things actually need to be shut down.

    This execution is normally scheduled by the signal handler.
    """

    logger.info("Stopping server for new HTTP connections")
    server.stop()

    # if event_publishers:
    #     logger.debug("Publishing application shutdown event")
    #     event_publishers.publish_event(Event(name=Events.BREWVIEW_STOPPED.name))
    #
    #     logger.info("Shutting down event publishers")
    #     await list(filter(lambda x: isinstance(x, Future), event_publishers.shutdown()))

    # We need to do this before the scheduler shuts down completely in order to kick any
    # currently waiting request creations
    logger.info("Closing all open HTTP connections")
    await server.close_all_connections()

    logger.info("Stopping IO loop")
    io_loop.add_callback(io_loop.stop)


def _setup_application():
    """Setup things that can be taken care of before io loop is started"""
    global io_loop, tornado_app, public_url, server, client_ssl

    # Tweak some config options
    web_config = beer_garden.config.get("web")
    web_config.url_prefix = normalize_url_prefix(web_config.url_prefix)

    auth_config = beer_garden.config.get("auth")
    if not auth_config.token.secret:
        auth_config.token.secret = os.urandom(20)
        if auth_config.enabled:
            logger.warning(
                "Brew-view was started with authentication enabled and no "
                "Secret. Generated tokens will not be valid across Brew-view "
                "restarts. To prevent this set the auth.token.secret config."
            )

    public_url = Url(
        scheme="https" if web_config.ssl.enabled else "http",
        host=web_config.public_fqdn,
        port=web_config.port,
        path=web_config.url_prefix,
    ).url

    tornado_app = _setup_tornado_app()
    server_ssl, client_ssl = _setup_ssl_context()

    server = HTTPServer(tornado_app, ssl_options=server_ssl)
    io_loop = IOLoop.current()


def _setup_tornado_app():
    # Import these here so we don't have a problem importing thrift_context
    import beer_garden.api.http.handlers.v1 as v1
    import beer_garden.api.http.handlers.v2 as v2
    import beer_garden.api.http.handlers.vbeta as vbeta
    import beer_garden.api.http.handlers.misc as misc

    web_config = beer_garden.config.get("web")
    prefix = web_config.url_prefix
    static_base = os.path.join(os.path.dirname(__file__), "static", "dist")

    # These get documented in our OpenAPI (fka Swagger) documentation
    published_url_specs = [
        # V1
        (rf"{prefix}api/v1/commands/?", v1.command.CommandListAPI),
        (rf"{prefix}api/v1/requests/?", v1.request.RequestListAPI),
        (rf"{prefix}api/v1/systems/?", v1.system.SystemListAPI),
        (rf"{prefix}api/v1/queues/?", v1.queue.QueueListAPI),
        (rf"{prefix}api/v1/users/?", v1.user.UsersAPI),
        (rf"{prefix}api/v1/roles/?", v1.role.RolesAPI),
        (rf"{prefix}api/v1/permissions/?", v1.permissions.PermissionsAPI),
        (rf"{prefix}api/v1/tokens/?", v1.token.TokenListAPI),
        (rf"{prefix}api/v1/admin/?", v1.admin.AdminAPI),
        (rf"{prefix}api/v1/jobs/?", v1.job.JobListAPI),
        (rf"{prefix}api/v1/commands/(\w+)/?", v1.command.CommandAPI),
        (rf"{prefix}api/v1/instances/(\w+)/?", v1.instance.InstanceAPI),
        (rf"{prefix}api/v1/requests/(\w+)/?", v1.request.RequestAPI),
        (rf"{prefix}api/v1/systems/(\w+)/?", v1.system.SystemAPI),
        (rf"{prefix}api/v1/queues/([\w\.-]+)/?", v1.queue.QueueAPI),
        (rf"{prefix}api/v1/users/(\w+)/?", v1.user.UserAPI),
        (rf"{prefix}api/v1/roles/(\w+)/?", v1.role.RoleAPI),
        (rf"{prefix}api/v1/tokens/(\w+)/?", v1.token.TokenAPI),
        (rf"{prefix}api/v1/jobs/(\w+)/?", v1.job.JobAPI),
        (rf"{prefix}api/v1/config/logging/?", v1.logging.LoggingConfigAPI),
        # Beta
        (rf"{prefix}api/vbeta/events/?", vbeta.event.EventPublisherAPI),
        # V2
        (rf"{prefix}api/v2/users/?", v1.user.UsersAPI),
        (rf"{prefix}api/v2/users/(\w+)/?", v1.user.UserAPI),
        (rf"{prefix}api/v2/tokens/?", v1.token.TokenListAPI),
        (rf"{prefix}api/v2/tokens/(\w+)/?", v1.token.TokenAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/admin/?", v2.admin.AdminAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/commands/?", v2.command.CommandListAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/commands/(\w+)/?", v2.command.CommandAPI),
        (
            rf"{prefix}api/v2/namespaces/(\w+)/instances/(\w+)/?",
            v2.instance.InstanceAPI,
        ),
        (rf"{prefix}api/v2/namespaces/(\w+)/jobs/?", v2.job.JobListAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/jobs/(\w+)/?", v2.job.JobAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/queues/?", v2.queue.QueueListAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/queues/([\w\.-]+)/?", v2.queue.QueueAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/requests/?", v2.request.RequestListAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/requests/(\w+)/?", v2.request.RequestAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/systems/?", v2.system.SystemListAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/systems/(\w+)/?", v2.system.SystemAPI),
        (rf"{prefix}api/v2/namespaces/(\w+)/events/?", v2.event.EventPublisherAPI),
    ]

    # And these do not
    unpublished_url_specs = [
        # These are a little special - unpublished but still versioned
        # The swagger spec
        (rf"{prefix}api/v1/spec/?", misc.SpecHandler),
        # Events websocket
        (rf"{prefix}api/v1/socket/events/?", v1.event.EventSocket),
        (rf"{prefix}api/v2/namespaces/(\w+)/events/socket/?", v2.event.EventSocket),
        # Version / configs
        (rf"{prefix}version/?", misc.VersionHandler),
        (rf"{prefix}config/?", misc.ConfigHandler),
        (rf"{prefix}config/swagger/?", misc.SwaggerConfigHandler),
        # Not sure if these are really necessary
        (rf"{prefix[:-1]}", RedirectHandler, {"url": prefix}),
        (
            rf"{prefix}swagger/(.*)",
            StaticFileHandler,
            {"path": os.path.join(static_base, "swagger")},
        ),
        # Static content
        (
            rf"{prefix}(.*)",
            StaticFileHandler,
            {"path": static_base, "default_filename": "index.html"},
        ),
    ]
    app_config = beer_garden.config.get("application")
    auth_config = beer_garden.config.get("auth")
    _load_swagger(published_url_specs, title=app_config.name)

    return Application(
        published_url_specs + unpublished_url_specs,
        debug=app_config.debug_mode,
        cookie_secret=auth_config.token.secret,
    )


def _setup_ssl_context():
    web_config = beer_garden.config.get("web")
    if web_config.ssl.enabled:
        server_ssl = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        server_ssl.load_cert_chain(
            certfile=web_config.ssl.public_key, keyfile=web_config.ssl.private_key
        )
        server_ssl.verify_mode = getattr(
            ssl, "CERT_" + web_config.ssl.client_cert_verify.upper()
        )

        client_ssl = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        client_ssl.load_cert_chain(
            certfile=web_config.ssl.public_key, keyfile=web_config.ssl.private_key
        )

        if web_config.ssl.ca_cert or web_config.ssl.ca_path:
            server_ssl.load_verify_locations(
                cafile=web_config.ssl.ca_cert, capath=web_config.ssl.ca_path
            )
            client_ssl.load_verify_locations(
                cafile=web_config.ssl.ca_cert, capath=web_config.ssl.ca_path
            )
    else:
        server_ssl = None
        client_ssl = None

    return server_ssl, client_ssl


# def _setup_event_publishers(ssl_context):
#     from brew_view.handlers.v1.event import EventSocket
#
#     # Create the collection of event publishers and add concrete publishers
#     pubs = EventPublishers(
#         {
#             "request": RequestPublisher(ssl_context=ssl_context),
#             "websocket": WebsocketPublisher(EventSocket),
#         }
#     )
#
#     if config.event.mongo.enable:
#         try:
#             pubs["mongo"] = MongoPublisher()
#         except Exception as ex:
#             logger.warning("Error starting Mongo event publisher: %s", ex)
#
#     if config.event.amq.enable:
#         try:
#             pika_params = {
#                 "host": config.amq.host,
#                 "port": config.amq.connections.message.port,
#                 "ssl": config.amq.connections.message.ssl,
#                 "user": config.amq.connections.admin.user,
#                 "password": config.amq.connections.admin.password,
#                 "exchange": config.event.amq.exchange,
#                 "virtual_host": config.event.amq.virtual_host,
#                 "connection_attempts": config.amq.connection_attempts,
#             }
#
#             # Make sure the exchange exists
#             TransientPikaClient(**pika_params).declare_exchange()
#
#             pubs["pika"] = TornadoPikaPublisher(
#                 shutdown_timeout=config.shutdown_timeout, **pika_params
#             )
#         except Exception as ex:
#             logger.exception("Error starting RabbitMQ event publisher: %s", ex)
#
#     # Metadata functions - additional metadata to be included with each event
#     pubs.metadata_funcs["public_url"] = lambda: public_url
#
#     return pubs


def _load_swagger(url_specs, title=None):

    global api_spec
    api_spec = APISpec(
        title=title,
        version="1.0",
        plugins=("apispec.ext.marshmallow", "apispec.ext.tornado"),
    )

    # Schemas from Marshmallow
    api_spec.definition("Parameter", schema=ParameterSchema)
    api_spec.definition("Command", schema=CommandSchema)
    api_spec.definition("Instance", schema=InstanceSchema)
    api_spec.definition("Request", schema=RequestSchema)
    api_spec.definition("System", schema=SystemSchema)
    api_spec.definition("LoggingConfig", schema=LoggingConfigSchema)
    api_spec.definition("Event", schema=EventSchema)
    api_spec.definition("User", schema=PrincipalSchema)
    api_spec.definition("Role", schema=RoleSchema)
    api_spec.definition("Queue", schema=QueueSchema)
    api_spec.definition("RefreshToken", schema=RefreshTokenSchema)
    api_spec.definition("_patch", schema=PatchSchema)
    api_spec.definition(
        "Patch",
        properties={
            "operations": {"type": "array", "items": {"$ref": "#/definitions/_patch"}}
        },
    )
    api_spec.definition("DateTrigger", schema=DateTriggerSchema)
    api_spec.definition("CronTrigger", schema=CronTriggerSchema)
    api_spec.definition("IntervalTrigger", schema=IntervalTriggerSchema)
    api_spec.definition("Job", schema=JobSchema)
    trigger_properties = {
        "allOf": [
            {"$ref": "#/definitions/CronTrigger"},
            {"$ref": "#/definitions/DateTrigger"},
            {"$ref": "#/definitions/IntervalTrigger"},
        ]
    }
    api_spec._definitions["Job"]["properties"]["trigger"] = trigger_properties

    error = {"message": {"type": "string"}}
    api_spec.definition(
        "400Error", properties=error, description="Parameter validation error"
    )
    api_spec.definition(
        "404Error", properties=error, description="Resource does not exist"
    )
    api_spec.definition(
        "409Error", properties=error, description="Resource already exists"
    )
    api_spec.definition("50xError", properties=error, description="Server exception")

    # Finally, add documentation for all our published paths
    for url_spec in url_specs:
        api_spec.add_path(urlspec=url_spec)
