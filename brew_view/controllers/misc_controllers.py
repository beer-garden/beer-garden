import logging

from tornado.gen import coroutine

import brew_view
from brew_view import thrift_context
from brew_view.base_handler import BaseHandler


class ConfigHandler(BaseHandler):

    def get(self):
        """Subset of configuration options that the frontend needs"""
        configs = {
            'allow_unsafe_templates': brew_view.config.application.allow_unsafe_templates,
            'application_name': brew_view.config.application.name,
            'amq_admin_port': brew_view.config.amq.connections.admin.port,
            'amq_host': brew_view.config.amq.host,
            'amq_port': brew_view.config.amq.connections.message.port,
            'amq_virtual_host': brew_view.config.amq.virtual_host,
            'backend_host': brew_view.config.backend.host,
            'backend_port': brew_view.config.backend.port,
            'icon_default': brew_view.config.application.icon_default,
            'debug_mode': brew_view.config.debug_mode,
            'url_prefix': brew_view.config.web.url_prefix,
            'metrics_url': brew_view.config.metrics.url,
            'auth_enabled': brew_view.config.auth.enabled,
        }
        self.write(configs)


class VersionHandler(BaseHandler):

    @coroutine
    def get(self):
        with thrift_context() as client:
            try:
                bartender_version = yield client.getVersion()
            except Exception as ex:
                logger = logging.getLogger(__name__)
                logger.error("Could not get Bartender Version.")
                logger.exception(ex)
                bartender_version = "unknown"

        self.write({
            "brew_view_version": brew_view.__version__,
            "bartender_version": bartender_version,
            "current_api_version": "v1",
            "supported_api_versions": ["v1"]
        })


class SwaggerConfigHandler(BaseHandler):

    def get(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write({
            'url': brew_view.config.web.url_prefix + 'api/v1/spec',
            'validatorUrl': None
        })


class SpecHandler(BaseHandler):

    def get(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(brew_view.api_spec.to_dict())
