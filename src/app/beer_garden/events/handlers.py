# -*- coding: utf-8 -*-
import logging

from brewtils.models import Events

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
from beer_garden.events.processors import BaseProcessor, InternalQueueListener

logger = logging.getLogger(__name__)


def error_event_handler(event):
    if event.error:
        logger.debug(
            f"ERROR EVENT SEEN:: Type: {event.name} Error Message:\n{event.error_message}"
        )


def add_internal_events_handler(event_manager):
    for event_config in [
        {
            "name": "Garden",
            "handler": beer_garden.garden.handle_event,
            "filter_func": beer_garden.garden.handle_event_filter,
            "filters": [
                Events.GARDEN_STARTED,
                Events.GARDEN_UPDATED,
                Events.GARDEN_STOPPED,
                Events.GARDEN_SYNC,
                Events.GARDEN_UNREACHABLE,
                Events.GARDEN_ERROR,
                Events.GARDEN_NOT_CONFIGURED,
                Events.GARDEN_CONFIGURED,
                Events.GARDEN_REMOVED,
                Events.GARDEN_CREATED,
                Events.ENTRY_STARTED,
            ],
            "local_only": False,
            "unique_data": True,
            "allow_api_only": False,
        },
        {
            "name": "Plugin",
            "handler": beer_garden.plugin.handle_event,
            "filter_func": None,
            "filters": [Events.INSTANCE_UPDATED],
            "local_only": False,
            "unique_data": True,
            "allow_api_only": False,
        },
        {
            "name": "Requests",
            "handler": beer_garden.requests.handle_event,
            "filter_func": beer_garden.requests.handle_event_filter,
            "filters": [
                Events.REQUEST_CREATED,
                Events.REQUEST_STARTED,
                Events.REQUEST_COMPLETED,
                Events.REQUEST_UPDATED,
                Events.REQUEST_CANCELED,
            ],
            "local_only": False,
            "unique_data": True,
            "allow_api_only": False,
        },
        {
            "name": "Publish Requests",
            "handler": beer_garden.publish_request.handle_event,
            "filter_func": beer_garden.publish_request.handle_event_filter,
            "filters": [
                Events.REQUEST_TOPIC_PUBLISH
            ],  # TODO: Determine if we need Events.REQUEST_CREATED
            "local_only": False,
            "unique_data": False,
            # Can not unique due to each Event potentially
            # spawning child Request operations
            "allow_api_only": False,
        },
        {
            "name": "Requests wait events",
            "handler": beer_garden.requests.handle_wait_events,
            "filter_func": beer_garden.requests.handle_wait_event_filter,
            "filters": [
                Events.REQUEST_COMPLETED,
                Events.REQUEST_CANCELED,
                Events.REQUEST_UPDATED,
                Events.GARDEN_STOPPED,
            ],
            "local_only": True,
            "unique_data": True,
            "allow_api_only": True,
        },
        {
            "name": "Router",
            "handler": beer_garden.router.handle_event,
            "filter_func": None,
            "filters": [
                Events.SYSTEM_CREATED,
                Events.SYSTEM_UPDATED,
                Events.GARDEN_SYNC,
                Events.GARDEN_CONFIGURED,
                Events.GARDEN_REMOVED,
                Events.GARDEN_UPDATED,
            ],
            "local_only": False,
            "unique_data": False,  # Can not unique due to API configurations
            "allow_api_only": False,
        },
        {
            "name": "System",
            "handler": beer_garden.systems.handle_event,
            "filter_func": None,
            "filters": [
                Events.SYSTEM_CREATED,
                Events.SYSTEM_UPDATED,
                Events.SYSTEM_REMOVED,
            ],
            "local_only": True,
            "unique_data": True,
            "allow_api_only": False,
        },
        {
            "name": "Scheduler",
            "handler": beer_garden.scheduler.handle_event,
            "filter_func": None,
            "filters": [
                Events.JOB_CREATED,
                Events.JOB_UPDATED,
                Events.JOB_PAUSED,
                Events.JOB_RESUMED,
                Events.JOB_DELETED,
                Events.JOB_EXECUTED,
                Events.DIRECTORY_FILE_CHANGE,
                Events.ENTRY_STARTED,
            ],
            "local_only": True,
            "unique_data": False,  # Can not unique due to Job Execute Events
            "allow_api_only": False,
        },
        {
            "name": "Log",
            "handler": beer_garden.log.handle_event,
            "filter_func": None,
            "filters": [Events.PLUGIN_LOGGER_FILE_CHANGE],
            "local_only": True,
            "unique_data": False,
            "allow_api_only": False,
        },
        {
            "name": "File",
            "handler": beer_garden.files.handle_event,
            "filter_func": beer_garden.files.handle_event_filter,
            "filters": [Events.JOB_CREATED, Events.REQUEST_CREATED],
            "local_only": True,
            "unique_data": True,
            "allow_api_only": False,
        },
        {
            "name": "Local plugins manager",
            "handler": beer_garden.local_plugins.manager.handle_event,
            "filter_func": None,
            "filters": [
                Events.INSTANCE_INITIALIZED,
                Events.INSTANCE_STOPPED,
                Events.ENTRY_STARTED,
            ],
            "local_only": True,
            "unique_data": False,  # Can not unique due to usage of metadata for rescans
            "allow_api_only": False,
        },
        {
            "name": "User event handler",
            "handler": beer_garden.user.handle_event,
            "filter_func": None,
            "filters": [Events.ROLE_DELETED, Events.USER_UPDATED],
            "local_only": True,
            # Can not unique due to ensure all user updates are handled correctly
            "unique_data": False,
            "allow_api_only": False,
        },
        {
            "name": "Replication event handler",
            "handler": beer_garden.replication.handle_event,
            "filter_func": None,
            "filters": [Events.REPLICATION_CREATED, Events.REPLICATION_UPDATED],
            "local_only": True,
            # Can not unique due to ensure all replication updates are handled correctly
            "unique_data": False,
            "allow_api_only": False,
        },
    ]:
        event_manager.register(InternalQueueListener(**event_config))

    event_manager.register(
        BaseProcessor(
            action=error_event_handler,
        )
    )
