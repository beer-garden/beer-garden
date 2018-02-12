import logging

from tornado.gen import coroutine

import brew_view
from brew_view import thrift_context
from brew_view.base_handler import BaseHandler


class ConfigHandler(BaseHandler):

    def get(self):
        """Subset of configuration options that the frontend needs"""
        self.write({k: brew_view.config[k] for k in
                    ['allow_unsafe_templates', 'application_name', 'amq_admin_port', 'amq_host',
                     'amq_port', 'amq_virtual_host', 'backend_host', 'backend_port', 'db_host',
                     'db_name', 'db_port', 'icon_default', 'debug_mode', 'url_prefix']})


class VersionHandler(BaseHandler):

    @coroutine
    def get(self):
        from brew_view._version import __version__

        with thrift_context() as client:
            try:
                bartender_version = yield client.getVersion()
            except Exception as ex:
                logger = logging.getLogger(__name__)
                logger.error("Could not get Bartender Version.")
                logger.exception(ex)
                bartender_version = "unknown"

        self.write({
            "brew_view_version": __version__,
            "bartender_version": bartender_version,
            "current_api_version": "v1",
            "supported_api_versions": ["v1"]
        })


class SwaggerConfigHandler(BaseHandler):

    def get(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write({
            'url': brew_view.config['url_prefix'] + 'api/v1/spec',
            'validatorUrl': None
        })


class SpecHandler(BaseHandler):

    def get(self):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(brew_view.api_spec.to_dict())
