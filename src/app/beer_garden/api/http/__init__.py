# -*- coding: utf-8 -*-
import logging
import os
import ssl
import types
from copy import deepcopy
from typing import Optional, Tuple

from apispec import APISpec
from brewtils.models import Event, Events, Principal
from brewtils.schemas import (
    CommandSchema,
    CronTriggerSchema,
    DateTriggerSchema,
    EventSchema,
    FileStatusSchema,
    GardenSchema,
    InstanceSchema,
    IntervalTriggerSchema,
    JobExportInputSchema,
    JobExportSchema,
    JobSchema,
    LegacyRoleSchema,
    LoggingConfigSchema,
    OperationSchema,
    ParameterSchema,
    PatchSchema,
    QueueSchema,
    RefreshTokenSchema,
    RequestSchema,
    RunnerSchema,
    SystemSchema,
    UserCreateSchema,
    UserListSchema,
    UserSchema,
)
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, RedirectHandler

import beer_garden
import beer_garden.api.http.handlers.misc as misc
import beer_garden.api.http.handlers.v1 as v1
import beer_garden.api.http.handlers.vbeta as vbeta
import beer_garden.config as config
import beer_garden.db.mongo.motor as moto
import beer_garden.events
import beer_garden.log
import beer_garden.requests
import beer_garden.router
from beer_garden.api.http.client import SerializeHelper
from beer_garden.api.http.processors import EventManager, websocket_publish
from beer_garden.api.http.schemas.v1.login import LoginInputSchema, LoginResponseSchema
from beer_garden.events import publish

io_loop: IOLoop = None
server: HTTPServer
tornado_app: Application
logger: logging.Logger = None
event_publishers = None
api_spec: APISpec
anonymous_principal: Principal
client_ssl: ssl.SSLContext


def run(ep_conn):
    global logger
    logger = logging.getLogger(__name__)

    _setup_application()
    _setup_event_handling(ep_conn)

    # Schedule things to happen after the ioloop comes up
    io_loop.add_callback(startup)

    logger.debug("Starting IO loop")
    io_loop.start()

    logger.info("Http entry point is shut down. Goodbye!")


def signal_handler(_: int, __: types.FrameType):
    io_loop.add_callback_from_signal(shutdown)


async def startup():
    """Do startup things.

    This is the first thing called from within the ioloop context.
    """
    global anonymous_principal

    http_config = config.get("entry.http")
    logger.debug(f"Starting HTTP server on {http_config.host}:{http_config.port}")
    server.listen(http_config.port, http_config.host)

    logger.info("Http entry point started")

    publish(
        Event(name=Events.ENTRY_STARTED.name, metadata={"entry_point_type": "HTTP"})
    )


async def shutdown():
    """Do shutdown things

    This still operates within the ioloop, so stopping it should be the last
    thing done.

    Because things in startup aren't guaranteed to have been run we need to be
    careful about checking to make sure things actually need to be shut down.

    This execution is normally scheduled by the signal handler.
    """

    logger.debug("Stopping server for new HTTP connections")
    server.stop()

    # This will almost definitely not be published to the websocket, because it would
    # need to make it up to the main process and back down into this process. We just
    # publish this here in case the main process is looking for it.
    publish(
        Event(name=Events.ENTRY_STOPPED.name, metadata={"entry_point_type": "HTTP"})
    )

    # We need to do this before the scheduler shuts down completely in order to kick any
    # currently waiting request creations
    logger.debug("Closing all open HTTP connections")
    await server.close_all_connections()

    logger.debug("Stopping IO loop")
    io_loop.add_callback(io_loop.stop)


def _setup_application():
    """Setup things that can be taken care of before io loop is started"""
    global io_loop, tornado_app, server, client_ssl

    io_loop = IOLoop.current()

    # Set up motor connection
    moto.create_connection(db_config=beer_garden.config.get("db"))

    auth_config = config.get("auth")
    if not auth_config.token_secret:
        auth_config.token_secret = os.urandom(20)
        if auth_config.enabled:
            logger.warning(
                "Brew-view was started with authentication enabled and no "
                "Secret. Generated tokens will not be valid across Brew-view "
                "restarts. To prevent this set the auth.token.secret config."
            )

    # This is only used for publishing events for external consumption (in v2 request
    # events were published with a link to the request, for example).
    # Commenting this out as it's not useful at the moment
    # from urllib3.util.url import Url
    #
    # http_config = config.get("entry.http")
    # public_url = Url(
    #     scheme="https" if http_config.ssl.enabled else "http",
    #     host=http_config.public_fqdn,
    #     port=http_config.port,
    #     path=http_config.url_prefix,
    # ).url

    tornado_app = _setup_tornado_app()
    server_ssl, client_ssl = _setup_ssl_context()

    server = HTTPServer(tornado_app, ssl_options=server_ssl)


def _setup_tornado_app() -> Application:
    prefix = config.get("entry.http.url_prefix")

    # These get documented in our OpenAPI (fka Swagger) documentation
    published_url_specs = [
        # V1
        (rf"{prefix}api/v1/requests/?", v1.request.RequestListAPI),
        (rf"{prefix}api/v1/systems/?", v1.system.SystemListAPI),
        (rf"{prefix}api/v1/queues/?", v1.queue.QueueListAPI),
        (rf"{prefix}api/v1/users/?", v1.user.UserListAPI),
        (rf"{prefix}api/v1/admin/?", v1.admin.AdminAPI),
        (rf"{prefix}api/v1/jobs/?", v1.job.JobListAPI),
        (rf"{prefix}api/v1/gardens/?", v1.garden.GardenListAPI),
        (rf"{prefix}api/v1/namespaces/?", v1.namespace.NamespaceListAPI),
        (rf"{prefix}api/v1/instances/(\w+)/?", v1.instance.InstanceAPI),
        (rf"{prefix}api/v1/instances/(\w+)/logs/?", v1.instance.InstanceLogAPI),
        (rf"{prefix}api/v1/instances/(\w+)/queues/?", v1.instance.InstanceQueuesAPI),
        (rf"{prefix}api/v1/requests/(\w+)/?", v1.request.RequestAPI),
        (rf"{prefix}api/v1/requests/output/(\w+)/?", v1.request.RequestOutputAPI),
        (rf"{prefix}api/v1/systems/(\w+)/commands/(\w+)/?", v1.command.CommandAPI),
        (rf"{prefix}api/v1/systems/(\w+)/?", v1.system.SystemAPI),
        (rf"{prefix}api/v1/queues/([\w\.-]+)/?", v1.queue.QueueAPI),
        (rf"{prefix}api/v1/users/(\w+)/?", v1.user.UserAPI),
        (rf"{prefix}api/v1/jobs/(\w+)/?", v1.job.JobAPI),
        (rf"{prefix}api/v1/logging/?", v1.logging.LoggingAPI),
        (rf"{prefix}api/v1/gardens/(.*)/?", v1.garden.GardenAPI),
        (rf"{prefix}api/v1/export/jobs/?", v1.job.JobExportAPI),
        (rf"{prefix}api/v1/import/jobs/?", v1.job.JobImportAPI),
        (rf"{prefix}api/v1/login", v1.login.LoginAPI),
        (rf"{prefix}api/v1/whoami", v1.user.WhoAmIAPI),
        # Beta
        (rf"{prefix}api/vbeta/events/?", vbeta.event.EventPublisherAPI),
        (rf"{prefix}api/vbeta/runners/?", vbeta.runner.RunnerListAPI),
        (rf"{prefix}api/vbeta/runners/(\w+)/?", vbeta.runner.RunnerAPI),
        (
            rf"{prefix}api/vbeta/chunks/?",
            beer_garden.api.http.handlers.vbeta.chunk.FileChunkAPI,
        ),
        (
            rf"{prefix}api/vbeta/chunks/id/?",
            beer_garden.api.http.handlers.vbeta.chunk.ChunkNameAPI,
        ),
        (rf"{prefix}api/vbeta/file/?", vbeta.file.RawFileListAPI),
        (rf"{prefix}api/vbeta/file/(\w+)/?", vbeta.file.RawFileAPI),
        # V2
        (rf"{prefix}api/v2/users/?", v1.user.UserListAPI),
        (rf"{prefix}api/v2/users/(\w+)/?", v1.user.UserAPI),
        # Deprecated
        (rf"{prefix}api/v1/commands/?", v1.command.CommandListAPI),
        (rf"{prefix}api/v1/commands/(\w+)/?", v1.command.CommandAPIOld),
        (rf"{prefix}api/v1/config/logging/?", v1.logging.LoggingConfigAPI),
    ]

    # And these do not
    unpublished_url_specs = [
        # These are a little special - unpublished but still versioned
        # The swagger spec
        (rf"{prefix}api/v1/spec/?", misc.SpecHandler),
        (rf"{prefix}api/v1/forward/?", v1.forward.ForwardAPI),
        # Events websocket
        (rf"{prefix}api/v1/socket/events/?", v1.event.EventSocket),
        # Version / configs
        (rf"{prefix}version/?", misc.VersionHandler),
        (rf"{prefix}config/?", misc.ConfigHandler),
        (rf"{prefix}config/swagger/?", misc.SwaggerConfigHandler),
        # Not sure if this is really necessary
        (rf"{prefix[:-1]}", RedirectHandler, {"url": prefix}),
    ]

    auth_config = config.get("auth")
    ui_config = config.get("ui")
    _load_swagger(published_url_specs, title=ui_config.name)

    return Application(
        published_url_specs + unpublished_url_specs,
        debug=ui_config.debug_mode,
        cookie_secret=auth_config.token_secret,
        autoreload=False,
        client=SerializeHelper(),
    )


def _setup_ssl_context() -> Tuple[Optional[ssl.SSLContext], Optional[ssl.SSLContext]]:
    http_config = config.get("entry.http")
    if http_config.ssl.enabled:
        server_ssl = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        server_ssl.load_cert_chain(
            certfile=http_config.ssl.public_key, keyfile=http_config.ssl.private_key
        )
        server_ssl.verify_mode = getattr(
            ssl, "CERT_" + http_config.ssl.client_cert_verify.upper()
        )

        client_ssl = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        client_ssl.load_cert_chain(
            certfile=http_config.ssl.public_key, keyfile=http_config.ssl.private_key
        )

        if http_config.ssl.ca_cert or http_config.ssl.ca_path:
            server_ssl.load_verify_locations(
                cafile=http_config.ssl.ca_cert, capath=http_config.ssl.ca_path
            )
            client_ssl.load_verify_locations(
                cafile=http_config.ssl.ca_cert, capath=http_config.ssl.ca_path
            )
    else:
        server_ssl = None
        client_ssl = None

    return server_ssl, client_ssl


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
    api_spec.definition("User", schema=UserSchema)
    api_spec.definition("UserCreate", schema=UserCreateSchema)
    api_spec.definition("UserList", schema=UserListSchema)
    api_spec.definition("Role", schema=LegacyRoleSchema)
    api_spec.definition("Queue", schema=QueueSchema)
    api_spec.definition("Operation", schema=OperationSchema)
    api_spec.definition("FileStatus", schema=FileStatusSchema)
    api_spec.definition("LoginInput", schema=LoginInputSchema)
    api_spec.definition("LoginResponse", schema=LoginResponseSchema)

    api_spec.definition("RefreshToken", schema=RefreshTokenSchema)

    api_spec.definition("Garden", schema=GardenSchema)
    api_spec.definition("Runner", schema=RunnerSchema)

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
    api_spec._definitions["Job"]["properties"]["trigger"] = trigger_properties  # noqa

    api_spec.definition("JobExport", schema=JobExportInputSchema)
    api_spec.definition("JobImport", schema=JobExportSchema)
    api_spec._definitions["JobImport"]["properties"][  # noqa
        "trigger"
    ] = trigger_properties

    error = {"message": {"type": "string"}}
    api_spec.definition(
        "400Error", properties=error, description="Parameter validation error"
    )
    api_spec.definition(
        "401Error", properties=error, description="Authorization required"
    )
    api_spec.definition("403Error", properties=error, description="Access denied")
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


def _setup_event_handling(ep_conn):
    # This will push all events generated in the entry point up to the master process
    beer_garden.events.manager = EventManager(ep_conn)

    # Add a handler to process events coming from the main process
    io_loop.add_handler(ep_conn, lambda c, _: _event_callback(c.recv()), IOLoop.READ)


def _event_callback(event):
    # Everything needs to be published to the websocket
    websocket_publish(event)

    # And also register handlers that the entry point needs to care about
    for handler in [
        beer_garden.router.handle_event,
        beer_garden.log.handle_event,
        beer_garden.requests.handle_event,
    ]:
        try:
            handler(deepcopy(event))
        except Exception as ex:
            logger.exception(f"Error executing callback for {event!r}: {ex}")
