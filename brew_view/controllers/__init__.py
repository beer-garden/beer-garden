# flake8: noqa
"""Module to make imports of Controllers easier"""
from brew_view.controllers.admin_api import AdminAPI, OldAdminAPI
from brew_view.controllers.command_api import CommandAPI
from brew_view.controllers.command_list_api import CommandListAPI
from brew_view.controllers.event_api import EventPublisherAPI, EventSocket
from brew_view.controllers.instance_api import InstanceAPI
from brew_view.controllers.job_api import JobAPI
from brew_view.controllers.job_list_api import JobListAPI
from brew_view.controllers.logging_api import LoggingConfigAPI
from brew_view.controllers.misc_controllers import (
    ConfigHandler, VersionHandler, SpecHandler, SwaggerConfigHandler
)
from brew_view.controllers.permissions_api import PermissionsAPI
from brew_view.controllers.queue_api import QueueAPI, OldQueueAPI
from brew_view.controllers.queue_list_api import QueueListAPI, OldQueueListAPI
from brew_view.controllers.request_api import RequestAPI
from brew_view.controllers.request_list_api import RequestListAPI
from brew_view.controllers.roles_api import RoleAPI, RolesAPI
from brew_view.controllers.system_api import SystemAPI
from brew_view.controllers.system_list_api import SystemListAPI
from brew_view.controllers.token_api import TokenAPI, TokenListAPI
from brew_view.controllers.users_api import UserAPI, UsersAPI
