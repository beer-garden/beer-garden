import contextlib
import json
import logging
import os
import ssl
from concurrent.futures import ThreadPoolExecutor
from io import open

from apispec import APISpec
from thriftpy.rpc import client_context
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler, RedirectHandler
from urllib3.util.url import Url

import bg_utils
import brewtils.rest
from bg_utils.event_publisher import EventPublishers
from bg_utils.pika import TransientPikaClient
from bg_utils.plugin_logging_loader import PluginLoggingLoader
from brew_view.publishers import MongoPublisher, RequestPublisher, TornadoPikaPublisher
from brew_view.specification import get_default_logging_config
from brewtils.schemas import ParameterSchema, CommandSchema, InstanceSchema, SystemSchema, \
    RequestSchema, PatchSchema, LoggingConfigSchema, EventSchema, QueueSchema

config = None
application = None
server = None
tornado_app = None
public_url = None
logger = None
thrift_context = None
event_publishers = None
api_spec = None
plugin_logging_config = None
app_log_config = None
notification_meta = None


def setup_brew_view(spec, cli_args):
    global config, logger, app_log_config, event_publishers, notification_meta

    # We load the config once just to see if there is a config file we should load
    temp_config = spec.load_config(cli_args, 'ENVIRONMENT')

    # If they specified a config file, we should load it up
    if temp_config.config:
        with open(temp_config.config) as config_file:
            config_from_file = json.load(config_file)
    else:
        config_from_file = {}

    config = spec.load_config(cli_args, config_from_file, 'ENVIRONMENT')

    # This is a little weird - just being slightly redundant here to avoid needing to change
    # application-configuration
    prefix = brewtils.rest.normalize_url_prefix(config.url_prefix)
    config['url_prefix'] = prefix
    config.url_prefix = prefix

    app_log_config = bg_utils.setup_application_logging(config,
                                                        get_default_logging_config(config.log_level,
                                                                                   config.log_file))
    logger = logging.getLogger(__name__)

    load_plugin_logging_config(config)
    bg_utils.setup_database(config)
    setup_application(config)


def load_plugin_logging_config(app_config):
    global plugin_logging_config

    plugin_logging_config = PluginLoggingLoader().load(
        filename=app_config.plugin_log_config,
        level=app_config.plugin_log_level,
        default_config=app_log_config
    )


def setup_application(app_config):
    global application, server, tornado_app, public_url, thrift_context, event_publishers

    public_url = Url(scheme='https' if config.ssl_enabled else 'http', host=config.public_fqdn,
                     port=config.web_port,
                     path=config.url_prefix).url

    thrift_context = _setup_thrift_context(app_config)
    tornado_app = _setup_tornado_app(app_config)
    server_ssl, client_ssl = _setup_ssl_context(app_config)
    event_publishers = _setup_event_publishers(app_config, client_ssl)

    server = HTTPServer(tornado_app, ssl_options=server_ssl)
    server.listen(app_config.web_port)

    application = IOLoop.current()


def _setup_tornado_app(app_config):

    # Import these here so we don't have a problem importing thrift_context
    from brew_view.controllers import AdminAPI, CommandAPI, CommandListAPI, ConfigHandler, \
        InstanceAPI, QueueAPI, QueueListAPI, RequestAPI, RequestListAPI, SystemAPI, SystemListAPI, \
        VersionHandler, SpecHandler, SwaggerConfigHandler, OldAdminAPI, OldQueueAPI, \
        OldQueueListAPI, LoggingConfigAPI, EventPublisherAPI

    static_base = os.path.join(os.path.dirname(__file__), 'static', 'dist')

    # These get documented in our OpenAPI (fka Swagger) documentation
    published_url_specs = [
        (r'{0}api/v1/commands/?'.format(app_config['url_prefix']), CommandListAPI),
        (r'{0}api/v1/commands/(\w+)/?'.format(app_config['url_prefix']), CommandAPI),
        (r'{0}api/v1/instances/(\w+)/?'.format(app_config['url_prefix']), InstanceAPI),
        (r'{0}api/v1/requests/?'.format(app_config['url_prefix']), RequestListAPI),
        (r'{0}api/v1/requests/(\w+)/?'.format(app_config['url_prefix']), RequestAPI),
        (r'{0}api/v1/systems/?'.format(app_config['url_prefix']), SystemListAPI),
        (r'{0}api/v1/systems/(\w+)/?'.format(app_config['url_prefix']), SystemAPI),
        (r'{0}api/v1/queues/?'.format(app_config['url_prefix']), QueueListAPI),
        (r'{0}api/v1/queues/([\w\.-]+)/?'.format(app_config['url_prefix']), QueueAPI),
        (r'{0}api/v1/admin/?'.format(app_config['url_prefix']), AdminAPI),
        (r'{0}api/v1/config/logging/?'.format(app_config['url_prefix']), LoggingConfigAPI),

        # Beta
        (r'{0}api/vbeta/events/?'.format(app_config['url_prefix']), EventPublisherAPI),

        # Deprecated
        (r'{0}api/v1/admin/system/?'.format(app_config['url_prefix']), OldAdminAPI),
        (r'{0}api/v1/admin/queues/?'.format(app_config['url_prefix']), OldQueueListAPI),
        (r'{0}api/v1/admin/queues/([\w\.-]+)/?'.format(app_config['url_prefix']), OldQueueAPI)
    ]

    # And these do not
    unpublished_url_specs = [
        (r'{0}config/?'.format(app_config['url_prefix']), ConfigHandler),
        (r'{0}config/swagger/?'.format(app_config['url_prefix']), SwaggerConfigHandler),
        (r'{0}version/?'.format(app_config['url_prefix']), VersionHandler),
        (r'{0}api/v1/spec/?'.format(app_config['url_prefix']), SpecHandler),
        (r'{0}'.format(app_config['url_prefix'][:-1]), RedirectHandler,
            {"url": app_config['url_prefix']}),
        (r'{0}swagger/(.*)'.format(app_config['url_prefix']), StaticFileHandler,
            {'path': os.path.join(static_base, 'swagger')}),
        (r'{0}(.*)'.format(app_config['url_prefix']), StaticFileHandler,
            {'path': static_base, 'default_filename': 'index.html'})
    ]
    _load_swagger(published_url_specs, title=app_config.application_name)

    return Application(published_url_specs + unpublished_url_specs, debug=app_config.debug_mode)


def _setup_ssl_context(app_config):

    if app_config.ssl_enabled:
        if app_config.client_cert_verify.upper() not in ('NONE', 'OPTIONAL', 'REQUIRED'):
            raise Exception('Resolved value for configuation client_cert_verify (%s) must be '
                            '"NONE", "OPTIONAL", or "REQUIRED"' % app_config.client_cert_verify)

        server_ssl = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        server_ssl.load_cert_chain(certfile=app_config.ssl_public_key,
                                   keyfile=app_config.ssl_private_key)
        server_ssl.verify_mode = getattr(ssl, 'CERT_'+app_config.client_cert_verify.upper())

        client_ssl = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        client_ssl.load_cert_chain(certfile=app_config.ssl_public_key,
                                   keyfile=app_config.ssl_private_key)

        if app_config.ca_cert or app_config.ca_path:
            server_ssl.load_verify_locations(cafile=app_config.ca_cert, capath=app_config.ca_path)
            client_ssl.load_verify_locations(cafile=app_config.ca_cert, capath=app_config.ca_path)
    else:
        server_ssl = None
        client_ssl = None

    return server_ssl, client_ssl


def _setup_thrift_context(app_config):

    class BgClient(object):
        """Helper class that wraps a thriftpy TClient"""

        executor = ThreadPoolExecutor(max_workers=10)

        def __init__(self, t_client):
            self.t_client = t_client

        def __getattr__(self, thrift_method):
            def submit(*args, **kwargs):
                return self.executor.submit(self.t_client.__getattr__(thrift_method),
                                            *args, **kwargs)
            return submit

    @contextlib.contextmanager
    def bg_thrift_context(async=True, **kwargs):
        with client_context(bg_utils.bg_thrift.BartenderBackend,
                            host=app_config.backend_host,
                            port=app_config.backend_port,
                            socket_timeout=app_config.backend_socket_timeout,
                            **kwargs) as client:
            yield BgClient(client) if async else client

    return bg_thrift_context


def _setup_event_publishers(app_config, ssl_context):

    # Create the collection of event publishers and add concrete publishers to it
    pubs = EventPublishers({'request': RequestPublisher(ssl_context=ssl_context)})

    if app_config.event_persist_mongo:
        pubs['mongo'] = MongoPublisher()

    if app_config.event_amq_virtual_host and app_config.event_amq_exchange:
        pika_params = {
            'host': app_config.amq_host, 'port': app_config.amq_port,
            'user': app_config.amq_admin_user,
            'password': app_config.amq_admin_password,
            'exchange': app_config.event_amq_exchange,
            'virtual_host': app_config.event_amq_virtual_host,
            'connection_attempts': app_config.amq_connection_attempts
        }

        # Make sure the exchange exists
        TransientPikaClient(**pika_params).declare_exchange()

        pubs['pika'] = TornadoPikaPublisher(
            shutdown_timeout=app_config.shutdown_timeout,
            **pika_params)

    # Add metadata functions - additional metadata that will be included with each event
    pubs.metadata_funcs['public_url'] = lambda: public_url

    return pubs


def _load_swagger(url_specs, title=None):

    global api_spec
    api_spec = APISpec(title=title, version='1.0',
                       plugins=('apispec.ext.marshmallow', 'apispec.ext.tornado'))

    # Schemas from Marshmallow
    api_spec.definition('Parameter', schema=ParameterSchema)
    api_spec.definition('Command', schema=CommandSchema)
    api_spec.definition('Instance', schema=InstanceSchema)
    api_spec.definition('Request', schema=RequestSchema)
    api_spec.definition('System', schema=SystemSchema)
    api_spec.definition('LoggingConfig', schema=LoggingConfigSchema)
    api_spec.definition('Event', schema=EventSchema)
    api_spec.definition('Queue', schema=QueueSchema)
    api_spec.definition('_patch', schema=PatchSchema)
    api_spec.definition('Patch', properties={"operations": {
        "type": "array", "items": {"$ref": "#/definitions/_patch"}}
    })

    error = {'message': {'type': 'string'}}
    api_spec.definition('400Error', properties=error, description='Parameter validation error')
    api_spec.definition('404Error', properties=error, description='Resource does not exist')
    api_spec.definition('409Error', properties=error, description='Resource already exists')
    api_spec.definition('50xError', properties=error, description='Server exception')

    # Finally, add documentation for all our published paths
    for url_spec in url_specs:
        api_spec.add_path(urlspec=url_spec)
