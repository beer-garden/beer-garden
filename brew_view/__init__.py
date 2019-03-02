import contextlib
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import ssl
from apispec import APISpec
from apscheduler.executors.tornado import TornadoExecutor
from apscheduler.schedulers.tornado import TornadoScheduler
from functools import partial
from prometheus_client.exposition import start_http_server
from pytz import utc
from thriftpy2.rpc import client_context
from tornado.concurrent import Future
from tornado.gen import coroutine, sleep
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler, RedirectHandler
from urllib3.util.url import Url

import bg_utils
import brew_view._version
from bg_utils.event_publisher import EventPublishers
from bg_utils.mongo import setup_database
from bg_utils.pika import TransientPikaClient
from bg_utils.plugin_logging_loader import PluginLoggingLoader
from brew_view.authorization import anonymous_principal as load_anonymous
from brew_view.metrics import initialize_counts
from brew_view.publishers import (
    MongoPublisher,
    RequestPublisher,
    TornadoPikaPublisher,
    WebsocketPublisher,
)
from brew_view.scheduler.jobstore import BGJobStore
from brew_view.specification import get_default_logging_config
from brewtils.models import Event, Events
from brewtils.rest import normalize_url_prefix
from brewtils.rest.easy_client import EasyClient
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

__version__ = brew_view._version.__version__

config = None
io_loop = None
server = None
tornado_app = None
public_url = None
logger = None
thrift_context = None
event_publishers = None
api_spec = None
plugin_logging_config = None
app_logging_config = None
notification_meta = None
request_scheduler = None
request_map = {}
anonymous_principal = None
easy_client = None
client_ssl = None


def setup(spec, cli_args):
    global config, logger, app_logging_config

    config = bg_utils.load_application_config(spec, cli_args)

    app_logging_config = bg_utils.setup_application_logging(
        config, get_default_logging_config(config.log.level, config.log.file)
    )
    logger = logging.getLogger(__name__)
    logger.debug("Logging configured. First post!")

    load_plugin_logging_config(config)
    _setup_application()


@coroutine
def startup():
    """Do startup things.

    This is the first thing called from within the ioloop context.
    """
    global event_publishers, anonymous_principal

    # Ensure we have a mongo connection
    logger.info("Checking for Mongo connection")
    yield _progressive_backoff(
        partial(setup_database, config), "Unable to connect to mongo, is it started?"
    )

    # Need to wait until after mongo connection established to load
    anonymous_principal = load_anonymous()

    logger.info("Starting event publishers")
    event_publishers = _setup_event_publishers(client_ssl)

    logger.info("Initializing metrics")
    initialize_counts()

    logger.info(
        "Starting metrics server on %s:%d" % (config.web.host, config.metrics.port)
    )
    start_http_server(config.metrics.port)

    logger.info("Starting HTTP server on %s:%d" % (config.web.host, config.web.port))
    server.listen(config.web.port, config.web.host)

    logger.info("Starting scheduler")
    request_scheduler.start()

    logger.debug("Publishing application startup event")
    event_publishers.publish_event(Event(name=Events.BREWVIEW_STARTED.name))

    brew_view.logger.info("Application is started. Hello!")


@coroutine
def shutdown():
    """Do shutdown things

    This still operates within the ioloop, so stopping it should be the last
    thing done.

    Because things in startup aren't guaranteed to have been run we need to be
    careful about checking to make sure things actually need to be shut down.

    This execution is normally scheduled by the signal handler.
    """
    if request_scheduler.running:
        logger.info("Stopping scheduler")
        request_scheduler.shutdown(wait=False)

    logger.info("Stopping HTTP server")
    server.stop()

    if event_publishers:
        logger.debug("Publishing application shutdown event")
        event_publishers.publish_event(Event(name=Events.BREWVIEW_STOPPED.name))

        logger.info("Shutting down event publishers")
        yield list(filter(lambda x: isinstance(x, Future), event_publishers.shutdown()))

    logger.info("Stopping IO loop")
    io_loop.add_callback(io_loop.stop)


@coroutine
def _progressive_backoff(func, failure_message):
    wait_time = 0.1
    while not func():
        logger.warning(failure_message)
        logger.warning("Waiting %.1f seconds before next attempt", wait_time)

        yield sleep(wait_time)
        wait_time = min(wait_time * 2, 30)


def load_plugin_logging_config(input_config):
    global plugin_logging_config

    plugin_logging_config = PluginLoggingLoader().load(
        filename=input_config.plugin_logging.config_file,
        level=input_config.plugin_logging.level,
        default_config=app_logging_config,
    )


def _setup_application():
    """Setup things that can be taken care of before io loop is started"""
    global io_loop, tornado_app, public_url, thrift_context, easy_client
    global server, client_ssl, request_scheduler

    # Tweak some config options
    config.web.url_prefix = normalize_url_prefix(config.web.url_prefix)
    if not config.auth.token.secret:
        config.auth.token.secret = os.urandom(20)
        if config.auth.enabled:
            logger.warning(
                "Brew-view was started with authentication enabled and no "
                "Secret. Generated tokens will not be valid across Brew-view "
                "restarts. To prevent this set the auth.token.secret config."
            )

    public_url = Url(
        scheme="https" if config.web.ssl.enabled else "http",
        host=config.web.public_fqdn,
        port=config.web.port,
        path=config.web.url_prefix,
    ).url

    # This is not super clean as we're pulling the config from different
    # 'sections,' but the scheduler is the only thing that uses this
    easy_client = EasyClient(
        host=config.web.public_fqdn,
        port=config.web.port,
        url_prefix=config.web.url_prefix,
        ssl_enabled=config.web.ssl.enabled,
        ca_cert=config.web.ssl.ca_cert,
        username=config.scheduler.auth.username,
        password=config.scheduler.auth.password,
    )

    thrift_context = _setup_thrift_context()
    tornado_app = _setup_tornado_app()
    server_ssl, client_ssl = _setup_ssl_context()
    request_scheduler = _setup_scheduler()

    server = HTTPServer(tornado_app, ssl_options=server_ssl)
    io_loop = IOLoop.current()


def _setup_scheduler():
    jobstores = {"beer_garden": BGJobStore()}
    # TODO: Look at creating a custom executor using process pools
    executors = {"default": TornadoExecutor(config.scheduler.max_workers)}
    job_defaults = config.scheduler.job_defaults.to_dict()

    return TornadoScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=utc,
    )


def _setup_tornado_app():

    # Import these here so we don't have a problem importing thrift_context
    from brew_view.controllers import (
        AdminAPI,
        CommandAPI,
        CommandListAPI,
        ConfigHandler,
        InstanceAPI,
        QueueAPI,
        QueueListAPI,
        RequestAPI,
        RequestListAPI,
        SystemAPI,
        SystemListAPI,
        VersionHandler,
        SpecHandler,
        SwaggerConfigHandler,
        OldAdminAPI,
        OldQueueAPI,
        OldQueueListAPI,
        LoggingConfigAPI,
        EventPublisherAPI,
        EventSocket,
        TokenAPI,
        UserAPI,
        UsersAPI,
        RoleAPI,
        RolesAPI,
        TokenListAPI,
        JobAPI,
        JobListAPI,
        PermissionsAPI,
    )

    prefix = config.web.url_prefix
    static_base = os.path.join(os.path.dirname(__file__), "static", "dist")

    # These get documented in our OpenAPI (fka Swagger) documentation
    published_url_specs = [
        (r"{0}api/v1/commands/?".format(prefix), CommandListAPI),
        (r"{0}api/v1/requests/?".format(prefix), RequestListAPI),
        (r"{0}api/v1/systems/?".format(prefix), SystemListAPI),
        (r"{0}api/v1/queues/?".format(prefix), QueueListAPI),
        (r"{0}api/v1/users/?".format(prefix), UsersAPI),
        (r"{0}api/v1/roles/?".format(prefix), RolesAPI),
        (r"{0}api/v1/permissions/?".format(prefix), PermissionsAPI),
        (r"{0}api/v1/tokens/?".format(prefix), TokenListAPI),
        (r"{0}api/v1/admin/?".format(prefix), AdminAPI),
        (r"{0}api/v1/jobs/?".format(prefix), JobListAPI),
        (r"{0}api/v1/commands/(\w+)/?".format(prefix), CommandAPI),
        (r"{0}api/v1/instances/(\w+)/?".format(prefix), InstanceAPI),
        (r"{0}api/v1/requests/(\w+)/?".format(prefix), RequestAPI),
        (r"{0}api/v1/systems/(\w+)/?".format(prefix), SystemAPI),
        (r"{0}api/v1/queues/([\w\.-]+)/?".format(prefix), QueueAPI),
        (r"{0}api/v1/users/(\w+)/?".format(prefix), UserAPI),
        (r"{0}api/v1/roles/(\w+)/?".format(prefix), RoleAPI),
        (r"{0}api/v1/tokens/(\w+)/?".format(prefix), TokenAPI),
        (r"{0}api/v1/jobs/(\w+)/?".format(prefix), JobAPI),
        (r"{0}api/v1/config/logging/?".format(prefix), LoggingConfigAPI),
        # Beta
        (r"{0}api/vbeta/events/?".format(prefix), EventPublisherAPI),
        # Deprecated
        (r"{0}api/v1/admin/system/?".format(prefix), OldAdminAPI),
        (r"{0}api/v1/admin/queues/?".format(prefix), OldQueueListAPI),
        (r"{0}api/v1/admin/queues/([\w\.-]+)/?".format(prefix), OldQueueAPI),
    ]

    # And these do not
    unpublished_url_specs = [
        # These are a little special - unpublished but still versioned
        # The swagger spec
        (r"{0}api/v1/spec/?".format(prefix), SpecHandler),
        # Events websocket
        (r"{0}api/v1/socket/events/?".format(prefix), EventSocket),
        # Version / configs
        (r"{0}version/?".format(prefix), VersionHandler),
        (r"{0}config/?".format(prefix), ConfigHandler),
        (r"{0}config/swagger/?".format(prefix), SwaggerConfigHandler),
        # Not sure if these are really necessary
        (r"{0}".format(prefix[:-1]), RedirectHandler, {"url": prefix}),
        (
            r"{0}swagger/(.*)".format(prefix),
            StaticFileHandler,
            {"path": os.path.join(static_base, "swagger")},
        ),
        # Static content
        (
            r"{0}(.*)".format(prefix),
            StaticFileHandler,
            {"path": static_base, "default_filename": "index.html"},
        ),
    ]
    _load_swagger(published_url_specs, title=config.application.name)

    return Application(
        published_url_specs + unpublished_url_specs,
        debug=config.debug_mode,
        cookie_secret=config.auth.token.secret,
    )


def _setup_ssl_context():

    if config.web.ssl.enabled:
        server_ssl = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        server_ssl.load_cert_chain(
            certfile=config.web.ssl.public_key, keyfile=config.web.ssl.private_key
        )
        server_ssl.verify_mode = getattr(
            ssl, "CERT_" + config.web.ssl.client_cert_verify.upper()
        )

        client_ssl = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        client_ssl.load_cert_chain(
            certfile=config.web.ssl.public_key, keyfile=config.web.ssl.private_key
        )

        if config.web.ssl.ca_cert or config.web.ssl.ca_path:
            server_ssl.load_verify_locations(
                cafile=config.web.ssl.ca_cert, capath=config.web.ssl.ca_path
            )
            client_ssl.load_verify_locations(
                cafile=config.web.ssl.ca_cert, capath=config.web.ssl.ca_path
            )
    else:
        server_ssl = None
        client_ssl = None

    return server_ssl, client_ssl


def _setup_thrift_context():
    class BgClient(object):
        """Helper class that wraps a thriftpy TClient"""

        executor = ThreadPoolExecutor(max_workers=10)

        def __init__(self, t_client):
            self.t_client = t_client

        def __getattr__(self, thrift_method):
            def submit(*args, **kwargs):
                return self.executor.submit(
                    self.t_client.__getattr__(thrift_method), *args, **kwargs
                )

            return submit

    @contextlib.contextmanager
    def bg_thrift_context(sync=False, **kwargs):
        with client_context(
            bg_utils.bg_thrift.BartenderBackend,
            host=config.backend.host,
            port=config.backend.port,
            socket_timeout=config.backend.socket_timeout,
            **kwargs
        ) as client:
            yield client if sync else BgClient(client)

    return bg_thrift_context


def _setup_event_publishers(ssl_context):
    from brew_view.controllers.event_api import EventSocket

    # Create the collection of event publishers and add concrete publishers
    pubs = EventPublishers(
        {
            "request": RequestPublisher(ssl_context=ssl_context),
            "websocket": WebsocketPublisher(EventSocket),
        }
    )

    if config.event.mongo.enable:
        try:
            pubs["mongo"] = MongoPublisher()
        except Exception as ex:
            logger.warning("Error starting Mongo event publisher: %s", ex)

    if config.event.amq.enable:
        try:
            pika_params = {
                "host": config.amq.host,
                "port": config.amq.connections.message.port,
                "ssl": config.amq.connections.message.ssl,
                "user": config.amq.connections.admin.user,
                "password": config.amq.connections.admin.password,
                "exchange": config.event.amq.exchange,
                "virtual_host": config.event.amq.virtual_host,
                "connection_attempts": config.amq.connection_attempts,
            }

            # Make sure the exchange exists
            TransientPikaClient(**pika_params).declare_exchange()

            pubs["pika"] = TornadoPikaPublisher(
                shutdown_timeout=config.shutdown_timeout, **pika_params
            )
        except Exception as ex:
            logger.exception("Error starting RabbitMQ event publisher: %s", ex)

    # Metadata functions - additional metadata to be included with each event
    pubs.metadata_funcs["public_url"] = lambda: public_url

    return pubs


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
