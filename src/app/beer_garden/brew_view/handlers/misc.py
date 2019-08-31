import logging

import beer_garden.brew_view
from beer_garden.brew_view.thrift import ThriftClient
from beer_garden.brew_view.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class ConfigHandler(BaseHandler):
    async def get(self):
        """Subset of configuration options that the frontend needs"""

        async with ThriftClient() as client:
            local_namespace = await client.getLocalNamespace()
            remote_namespaces = await client.getRemoteNamespaces()

        configs = {
            "allow_unsafe_templates": beer_garden.brew_view.config.application.allow_unsafe_templates,
            "application_name": beer_garden.brew_view.config.application.name,
            "icon_default": beer_garden.brew_view.config.application.icon_default,
            "debug_mode": beer_garden.brew_view.config.application.debug_mode,
            "url_prefix": beer_garden.brew_view.config.web.url_prefix,
            "metrics_url": beer_garden.brew_view.config.metrics.prometheus.url,
            "auth_enabled": beer_garden.brew_view.config.auth.enabled,
            "guest_login_enabled": beer_garden.brew_view.config.auth.guest_login_enabled,
            "namespaces": {"local": local_namespace, "remote": remote_namespaces},
        }

        self.write(configs)


class VersionHandler(BaseHandler):
    async def get(self):
        try:
            async with ThriftClient() as client:
                bartender_version = await client.getVersion()
        except Exception as ex:
            logger.exception(f"Error determining Bartender version - Caused by:\n{ex}")
            bartender_version = "unknown"

        self.write(
            {
                "brew_view_version": beer_garden.__version__,
                "bartender_version": bartender_version,
                "current_api_version": "v1",
                "supported_api_versions": ["v1"],
            }
        )


class SwaggerConfigHandler(BaseHandler):
    def get(self):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(
            {
                "url": beer_garden.brew_view.config.web.url_prefix + "api/v1/spec",
                "validatorUrl": None,
            }
        )


class SpecHandler(BaseHandler):
    def get(self):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(beer_garden.brew_view.api_spec.to_dict())
