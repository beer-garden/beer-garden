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
    for handler, handler_tag, local_only, filters, unique_data, filter_func in [
        (
            beer_garden.garden.handle_event,
            "Garden",
            False,
            [
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
                Events.SYSTEM_CREATED,
                Events.SYSTEM_UPDATED,
                Events.SYSTEM_REMOVED,
                Events.INSTANCE_INITIALIZED,
                Events.INSTANCE_STARTED,
                Events.INSTANCE_UPDATED,
                Events.INSTANCE_STOPPED,
                Events.ENTRY_STARTED,
            ],
            True,
            None,
        ),
        (
            beer_garden.plugin.handle_event,
            "Plugin",
            False,
            [Events.INSTANCE_UPDATED],
            True,
            None,
        ),
        (
            beer_garden.requests.handle_event,
            "Requests",
            False,
            [
                Events.REQUEST_CREATED,
                Events.REQUEST_STARTED,
                Events.REQUEST_COMPLETED,
                Events.REQUEST_UPDATED,
                Events.REQUEST_CANCELED,
            ],
            True,
            beer_garden.requests.handle_event_filter,
        ),
        (
            beer_garden.publish_request.handle_event,
            "Publish Requests",
            False,
            [Events.REQUEST_TOPIC_PUBLISH, Events.REQUEST_CREATED],
            False,
            None,
            # Can not unique due to each Event potentially
            # spawning child Request operations
        ),
        (
            beer_garden.requests.handle_wait_events,
            "Requests wait events",
            False,
            [Events.REQUEST_COMPLETED, Events.REQUEST_CANCELED, Events.GARDEN_STOPPED],
            True,
            None,
        ),
        (
            beer_garden.router.handle_event,
            "Router",
            False,
            [
                Events.SYSTEM_CREATED,
                Events.SYSTEM_UPDATED,
                Events.GARDEN_SYNC,
                Events.GARDEN_CONFIGURED,
                Events.GARDEN_REMOVED,
                Events.GARDEN_UPDATED,
            ],
            False,  # Can not unique due to API configurations
            None,
        ),
        (
            beer_garden.systems.handle_event,
            "System",
            True,
            [Events.SYSTEM_CREATED, Events.SYSTEM_UPDATED, Events.SYSTEM_REMOVED],
            True,
            None,
        ),
        (
            beer_garden.scheduler.handle_event,
            "Scheduler",
            True,
            [
                Events.JOB_CREATED,
                Events.JOB_UPDATED,
                Events.JOB_PAUSED,
                Events.JOB_RESUMED,
                Events.JOB_DELETED,
                Events.JOB_EXECUTED,
                Events.DIRECTORY_FILE_CHANGE,
            ],
            False,  # Can not unique due to Job Execute Events
            None,
        ),
        (
            beer_garden.log.handle_event,
            "Log",
            True,
            [Events.PLUGIN_LOGGER_FILE_CHANGE],
            False,
            None,
        ),
        (
            beer_garden.files.handle_event,
            "File",
            True,
            [Events.JOB_CREATED, Events.REQUEST_CREATED],
            True,
            None,
        ),
        (
            beer_garden.local_plugins.manager.handle_event,
            "Local plugins manager",
            True,
            [
                Events.INSTANCE_INITIALIZED,
                Events.INSTANCE_STOPPED,
                Events.ENTRY_STARTED,
            ],
            False,  # Can not unique due to usage of metadata for rescans
            None,
        ),
        (
            beer_garden.user.handle_event,
            "User event handler",
            True,
            [Events.ROLE_DELETED, Events.USER_UPDATED],
            False,  # Can not unique due to ensure all user updates are handled correctly
            None,
        ),
        (
            beer_garden.replication.handle_event,
            "Replication event handler",
            True,
            [Events.REPLICATION_CREATED, Events.REPLICATION_UPDATED],
            False,  # Can not unique due to ensure all replication updates are handled correctly
            None,
        ),
    ]:
        event_manager.register(
            InternalQueueListener(
                handler=handler,
                handler_tag=handler_tag,
                filters=filters,
                local_only=local_only,
                name=handler_tag,
                unique_data=unique_data,
                filter_func=filter_func,
            )
        )

    event_manager.register(
        BaseProcessor(
            action=error_event_handler,
        )
    )
