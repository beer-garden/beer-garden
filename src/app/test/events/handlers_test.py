# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Events
from mock import Mock

from beer_garden.events.handlers import add_internal_events_handler
from beer_garden.events.processors import FanoutProcessor
from beer_garden import config

class TestHandlers:
    @pytest.mark.parametrize(
        "event_name,expected_calls",
        [
            (Events.BREWVIEW_STARTED, 0),
            (Events.BREWVIEW_STOPPED, 0),
            (Events.BARTENDER_STARTED, 0),
            (Events.BARTENDER_STOPPED, 0),
            (Events.REQUEST_CREATED, 3),
            (Events.REQUEST_STARTED, 1),
            (Events.REQUEST_UPDATED, 1),
            (Events.REQUEST_COMPLETED, 2),
            (Events.REQUEST_CANCELED, 2),
            (Events.REQUEST_TOPIC_PUBLISH, 1),
            (Events.REQUEST_DELETED, 0),
            (Events.INSTANCE_INITIALIZED, 2),
            (Events.INSTANCE_STARTED, 1),
            (Events.INSTANCE_UPDATED, 2),
            (Events.INSTANCE_STOPPED, 2),
            (Events.SYSTEM_CREATED, 3),
            (Events.SYSTEM_UPDATED, 3),
            (Events.SYSTEM_REMOVED, 2),
            (Events.QUEUE_CLEARED, 0),
            (Events.ALL_QUEUES_CLEARED, 0),
            (Events.DB_CREATE, 0),
            (Events.DB_UPDATE, 0),
            (Events.DB_DELETE, 0),
            (Events.GARDEN_CREATED, 1),
            (Events.GARDEN_CONFIGURED, 2),
            (Events.GARDEN_UPDATED, 2),
            (Events.GARDEN_REMOVED, 2),
            (Events.FILE_CREATED, 0),
            (Events.GARDEN_STARTED, 1),
            (Events.GARDEN_STOPPED, 2),
            (Events.GARDEN_UNREACHABLE, 1),
            (Events.GARDEN_ERROR, 1),
            (Events.GARDEN_NOT_CONFIGURED, 1),
            (Events.GARDEN_SYNC, 3),
            (Events.ENTRY_STARTED, 1),
            (Events.ENTRY_STOPPED, 0),
            (Events.JOB_CREATED, 2),
            (Events.JOB_DELETED, 1),
            (Events.JOB_PAUSED, 1),
            (Events.JOB_RESUMED, 1),
            (Events.PLUGIN_LOGGER_FILE_CHANGE, 1),
            (Events.RUNNER_STARTED, 0),
            (Events.RUNNER_STOPPED, 0),
            (Events.RUNNER_REMOVED, 0),
            (Events.JOB_UPDATED, 1),
            (Events.JOB_EXECUTED, 1),
            (Events.USER_UPDATED, 1),
            (Events.USERS_IMPORTED, 0),
            (Events.ROLE_UPDATED, 0),
            (Events.ROLE_DELETED, 1),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_SYNC, 0),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_REMOVE, 0),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_UPDATE, 0),
            (Events.TOPIC_CREATED, 0),
            (Events.TOPIC_UPDATED, 0),
            (Events.TOPIC_REMOVED, 0),
            (Events.REPLICATION_CREATED, 1),
            (Events.REPLICATION_UPDATED, 1),
            (Events.DIRECTORY_FILE_CHANGE, 1),
        ],
    )
    def test_garden_local_callbacks(self, monkeypatch, bg_event, event_name, expected_calls):
        """garden_ballbacks should send a copy of event to handlers as to not mangle it"""

        bg_event.name = event_name.name
        bg_event.garden = "localgarden"

        config._CONFIG = {"garden": {"name": bg_event.garden}}        

        event_manager = FanoutProcessor(name="event manager")
        add_internal_events_handler(event_manager)

        assert len(event_manager._managed_processors) == 15
        
        put_mock = Mock()

        for processor in event_manager._managed_processors:
           
            monkeypatch.setattr(processor._queue, "put", put_mock)
            processor.put(bg_event)


        assert put_mock.call_count == expected_calls

    @pytest.mark.parametrize(
        "event_name,expected_calls",
        [
            (Events.BREWVIEW_STARTED, 0),
            (Events.BREWVIEW_STOPPED, 0),
            (Events.BARTENDER_STARTED, 0),
            (Events.BARTENDER_STOPPED, 0),
            (Events.REQUEST_CREATED, 2),
            (Events.REQUEST_STARTED, 1),
            (Events.REQUEST_UPDATED, 1),
            (Events.REQUEST_COMPLETED, 2),
            (Events.REQUEST_CANCELED, 2),
            (Events.REQUEST_TOPIC_PUBLISH, 1),
            (Events.REQUEST_DELETED, 0),
            (Events.INSTANCE_INITIALIZED, 1),
            (Events.INSTANCE_STARTED, 1),
            (Events.INSTANCE_UPDATED, 2),
            (Events.INSTANCE_STOPPED, 1),
            (Events.SYSTEM_CREATED, 2),
            (Events.SYSTEM_UPDATED, 2),
            (Events.SYSTEM_REMOVED, 1),
            (Events.QUEUE_CLEARED, 0),
            (Events.ALL_QUEUES_CLEARED, 0),
            (Events.DB_CREATE, 0),
            (Events.DB_UPDATE, 0),
            (Events.DB_DELETE, 0),
            (Events.GARDEN_CREATED, 1),
            (Events.GARDEN_CONFIGURED, 2),
            (Events.GARDEN_UPDATED, 2),
            (Events.GARDEN_REMOVED, 2),
            (Events.FILE_CREATED, 0),
            (Events.GARDEN_STARTED, 1),
            (Events.GARDEN_STOPPED, 2),
            (Events.GARDEN_UNREACHABLE, 1),
            (Events.GARDEN_ERROR, 1),
            (Events.GARDEN_NOT_CONFIGURED, 1),
            (Events.GARDEN_SYNC, 2),
            (Events.ENTRY_STARTED, 0),
            (Events.ENTRY_STOPPED, 0),
            (Events.JOB_CREATED, 0),
            (Events.JOB_DELETED, 0),
            (Events.JOB_PAUSED, 0),
            (Events.JOB_RESUMED, 0),
            (Events.PLUGIN_LOGGER_FILE_CHANGE, 0),
            (Events.RUNNER_STARTED, 0),
            (Events.RUNNER_STOPPED, 0),
            (Events.RUNNER_REMOVED, 0),
            (Events.JOB_UPDATED, 0),
            (Events.JOB_EXECUTED,0),
            (Events.USER_UPDATED, 0),
            (Events.USERS_IMPORTED, 0),
            (Events.ROLE_UPDATED, 0),
            (Events.ROLE_DELETED, 0),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_SYNC, 0),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_REMOVE, 0),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_UPDATE, 0),
            (Events.TOPIC_CREATED, 0),
            (Events.TOPIC_UPDATED, 0),
            (Events.TOPIC_REMOVED, 0),
            (Events.REPLICATION_CREATED, 0),
            (Events.REPLICATION_UPDATED, 0),
            (Events.DIRECTORY_FILE_CHANGE, 0),
        ],
    )
    def test_garden_remote_callbacks(self, monkeypatch, bg_event, event_name, expected_calls):
        """garden_ballbacks should send a copy of event to handlers as to not mangle it"""

        bg_event.name = event_name.name
        bg_event.garden = "remotegarden"

        config._CONFIG = {"garden": {"name": "localgarden"}}        

        event_manager = FanoutProcessor(name="event manager")
        add_internal_events_handler(event_manager)

        assert len(event_manager._managed_processors) == 15
        
        put_mock = Mock()

        for processor in event_manager._managed_processors:
           
            monkeypatch.setattr(processor._queue, "put", put_mock)
            processor.put(bg_event)


        assert put_mock.call_count == expected_calls
