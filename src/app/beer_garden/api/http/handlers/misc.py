import logging

from brewtils import normalize_url_prefix

import beer_garden.api.http
from beer_garden.api.http.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class ConfigHandler(BaseHandler):
    async def get(self):
        """Subset of configuration options that the frontend needs"""

        local_namespace = await self.client.get_local_namespace()
        remote_namespaces = await self.client.get_remote_namespaces()

        app_config = beer_garden.config.get("application")
        http_config = beer_garden.config.get("entry.http")
        metrics_config = beer_garden.config.get("metrics")
        auth_config = beer_garden.config.get("auth")
        configs = {
            "allow_unsafe_templates": app_config.allow_unsafe_templates,
            "application_name": app_config.name,
            "icon_default": app_config.icon_default,
            "debug_mode": app_config.debug_mode,
            "url_prefix": normalize_url_prefix(http_config.url_prefix),
            "metrics_url": metrics_config.prometheus.url,
            "auth_enabled": auth_config.enabled,
            "guest_login_enabled": auth_config.guest_login_enabled,
            "namespaces": {"local": local_namespace, "remote": remote_namespaces},
        }

        self.write(configs)


class VersionHandler(BaseHandler):
    async def get(self):
        try:
            version = await self.client.get_version()
        except Exception as ex:
            logger.exception(f"Error determining version - Caused by:\n{ex}")
            version = "unknown"

        self.write(
            {
                "brew_view_version": beer_garden.__version__,
                "bartender_version": version,
                "current_api_version": "v1",
                "supported_api_versions": ["v1"],
            }
        )


class SwaggerConfigHandler(BaseHandler):
    def get(self):
        prefix = normalize_url_prefix(beer_garden.config.get("entry.http.url_prefix"))
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write({"url": f"{prefix}api/v1/spec", "validatorUrl": None})


class SpecHandler(BaseHandler):
    def get(self):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(beer_garden.api.http.api_spec.to_dict())
