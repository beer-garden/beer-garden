# -*- coding: utf-8 -*-
import logging
import traceback
from copy import deepcopy

import elasticapm
from brewtils.models import Event

import beer_garden.config
import beer_garden.config as config
import beer_garden.files
import beer_garden.garden
import beer_garden.local_plugins.manager
import beer_garden.log
import beer_garden.plugin
import beer_garden.publish_request
import beer_garden.replication
import beer_garden.requests
import beer_garden.role
import beer_garden.router
import beer_garden.scheduler
import beer_garden.systems
import beer_garden.topic
import beer_garden.user
from beer_garden.events.processors import InternalQueueListener

logger = logging.getLogger(__name__)


def add_internal_events_handler(event_manager):
    for handler, handler_tag, filters in [
        (beer_garden.application.handle_event, "Application", []),
        (beer_garden.garden.handle_event, "Garden", []),
        (beer_garden.plugin.handle_event, "Plugin", []),
        (beer_garden.requests.handle_event, "Requests", []),
        (beer_garden.publish_request.handle_event, "Publish Requests", []),
        (beer_garden.requests.handle_wait_events, "Requests wait events", []),
        (beer_garden.router.handle_event, "Router", []),
        (beer_garden.systems.handle_event, "System", []),
        (beer_garden.scheduler.handle_event, "Scheduler", []),
        (beer_garden.topic.handle_event, "Topic", []),
        (beer_garden.log.handle_event, "Log", []),
        (beer_garden.files.handle_event, "File", []),
        (beer_garden.local_plugins.manager.handle_event, "Local plugins manager", []),
        (beer_garden.user.handle_event, "User event handler", []),
        (beer_garden.role.handle_event, "Role event handler", []),
        (beer_garden.replication.handle_event, "Replication event handler", []),
    ]:
        event_manager.register(
            InternalQueueListener(
                handler=handler,
                handler_tag=handler_tag,
                filters=filters,
                name=handler_tag,
            )
        )
