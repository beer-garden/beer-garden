# -*- coding: utf-8 -*-
import logging

import beer_garden.api.http
import beer_garden.config as config
from beer_garden.api.http.base_handler import BaseHandler

logger = logging.getLogger(__name__)


class ConfigHandler(BaseHandler):
    async def get(self):
        """Subset of configuration options that the frontend needs"""
        auth_config = config.get("auth")
        trusted_header_config = auth_config.authentication_handlers.trusted_header
        ui_config = config.get("ui")

        configs = {
            "application_name": ui_config.name,
            "auth_enabled": auth_config.enabled,
            "trusted_header_auth_enabled": trusted_header_config.enabled,
            "icon_default": ui_config.icon_default,
            "debug_mode": ui_config.debug_mode,
            "execute_javascript": ui_config.execute_javascript,
            "auto_refresh": ui_config.auto_refresh,
            "garden_name": config.get("garden.name"),
            "metrics_url": config.get("metrics.prometheus.url"),
            "url_prefix": config.get("entry.http.url_prefix"),
            "action_ttl": config.get("db.ttl.action"),
            "info_ttl": config.get("db.ttl.info"),
        }

        self.write(configs)


class VersionHandler(BaseHandler):
    async def get(self):
        self.write(
            {
                "beer_garden_version": beer_garden.__version__,
                "current_api_version": "v1",
                "supported_api_versions": ["v1"],
            }
        )


class SwaggerConfigHandler(BaseHandler):
    def get(self):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(
            {
                "url": f"{config.get('entry.http.url_prefix')}api/v1/spec",
                "validatorUrl": None,
            }
        )


class SpecHandler(BaseHandler):
    def get(self):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(beer_garden.api.http.api_spec.to_dict())
