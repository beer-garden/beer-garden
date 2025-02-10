# -*- coding: utf-8 -*-
from copy import deepcopy

import pytest
from brewtils.models import Events
from mock import Mock

from beer_garden import config
from beer_garden.events.handlers import add_internal_events_handler
from beer_garden.events.processors import FanoutProcessor


class TestHandlers:

    @pytest.fixture(autouse=True)
    def load_config(self):
        config._CONFIG = {
            "events_handler": {
                "file": {"enabled": True, "unique_data": False},
                "garden": {"enabled": True, "unique_data": False},
                "plugin": {"enabled": True, "unique_data": False},
                "requests": {"enabled": True, "unique_data": False},
                "system": {"enabled": True, "unique_data": False},
            },
            "plugin": {"local": {"directory": "/tmp"}},
        }

    @pytest.mark.parametrize(
        "event_name,expected_calls,trigger_event",
        [
            (Events.BREWVIEW_STARTED, 0, False),
            (Events.BREWVIEW_STOPPED, 0, False),
            (Events.BARTENDER_STARTED, 0, False),
            (Events.BARTENDER_STOPPED, 0, False),
            (Events.REQUEST_CREATED, 3, False),
            (Events.REQUEST_STARTED, 1, False),
            (Events.REQUEST_UPDATED, 1, False),
            (Events.REQUEST_COMPLETED, 2, False),
            (Events.REQUEST_CANCELED, 2, False),
            (Events.REQUEST_TOPIC_PUBLISH, 1, False),
            (Events.REQUEST_DELETED, 0, False),
            (Events.INSTANCE_INITIALIZED, 1, True),
            (Events.INSTANCE_STARTED, 0, True),
            (Events.INSTANCE_UPDATED, 1, True),
            (Events.INSTANCE_STOPPED, 1, True),
            (Events.SYSTEM_CREATED, 2, True),
            (Events.SYSTEM_UPDATED, 2, True),
            (Events.SYSTEM_REMOVED, 1, True),
            (Events.QUEUE_CLEARED, 0, False),
            (Events.ALL_QUEUES_CLEARED, 0, False),
            (Events.DB_CREATE, 0, False),
            (Events.DB_UPDATE, 0, False),
            (Events.DB_DELETE, 0, False),
            (Events.GARDEN_CREATED, 1, False),
            (Events.GARDEN_CONFIGURED, 2, False),
            (Events.GARDEN_UPDATED, 2, False),
            (Events.GARDEN_REMOVED, 2, False),
            (Events.FILE_CREATED, 0, False),
            (Events.GARDEN_STARTED, 1, False),
            (Events.GARDEN_STOPPED, 2, False),
            (Events.GARDEN_UNREACHABLE, 1, False),
            (Events.GARDEN_ERROR, 1, False),
            (Events.GARDEN_NOT_CONFIGURED, 1, False),
            (Events.GARDEN_SYNC, 2, False),
            (Events.ENTRY_STARTED, 1, False),
            (Events.ENTRY_STOPPED, 0, False),
            (Events.JOB_CREATED, 2, False),
            (Events.JOB_DELETED, 1, False),
            (Events.JOB_PAUSED, 1, False),
            (Events.JOB_RESUMED, 1, False),
            (Events.PLUGIN_LOGGER_FILE_CHANGE, 1, False),
            (Events.RUNNER_STARTED, 0, False),
            (Events.RUNNER_STOPPED, 0, False),
            (Events.RUNNER_REMOVED, 0, False),
            (Events.JOB_UPDATED, 1, False),
            (Events.JOB_EXECUTED, 1, False),
            (Events.USER_UPDATED, 1, False),
            (Events.USERS_IMPORTED, 0, False),
            (Events.ROLE_UPDATED, 0, False),
            (Events.ROLE_DELETED, 1, False),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_SYNC, 0, False),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_REMOVE, 0, False),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_UPDATE, 0, False),
            (Events.TOPIC_CREATED, 0, False),
            (Events.TOPIC_UPDATED, 0, False),
            (Events.TOPIC_REMOVED, 0, False),
            (Events.REPLICATION_CREATED, 1, False),
            (Events.REPLICATION_UPDATED, 1, False),
            (Events.DIRECTORY_FILE_CHANGE, 1, False),
        ],
    )
    def test_garden_local_callbacks(
        self, monkeypatch, bg_event, event_name, expected_calls, trigger_event
    ):
        """Tests to ensure the expected number of Handlers are called for local events"""

        bg_event.name = event_name.name
        bg_event.garden = "localgarden"

        config._CONFIG["garden"] = {"name": bg_event.garden}

        event_manager = FanoutProcessor(name="event manager")
        add_internal_events_handler(event_manager)

        assert len(event_manager._managed_processors) == 15

        queue_mock = Mock()
        append_mock = Mock()
        queue_mock.append = append_mock

        for processor in event_manager._managed_processors:
            if hasattr(processor, "_trigger_event"):
                assert processor._trigger_event is None

        for processor in event_manager._managed_processors:

            if hasattr(processor, "_queue"):
                monkeypatch.setattr(processor, "_queue", queue_mock)

            processor.put(bg_event)

        for processor in event_manager._managed_processors:
            if hasattr(processor, "_trigger_event"):
                if trigger_event:
                    assert processor._trigger_event is not None
                else:
                    assert processor._trigger_event is None

        assert append_mock.call_count == expected_calls

    @pytest.mark.parametrize(
        "event_name,expected_calls,trigger_event",
        [
            (Events.BREWVIEW_STARTED, 0, False),
            (Events.BREWVIEW_STOPPED, 0, False),
            (Events.BARTENDER_STARTED, 0, False),
            (Events.BARTENDER_STOPPED, 0, False),
            (Events.REQUEST_CREATED, 2, False),
            (Events.REQUEST_STARTED, 1, False),
            (Events.REQUEST_UPDATED, 1, False),
            (Events.REQUEST_COMPLETED, 2, False),
            (Events.REQUEST_CANCELED, 2, False),
            (Events.REQUEST_TOPIC_PUBLISH, 1, False),
            (Events.REQUEST_DELETED, 0, False),
            (Events.INSTANCE_INITIALIZED, 0, True),
            (Events.INSTANCE_STARTED, 0, True),
            (Events.INSTANCE_UPDATED, 1, True),
            (Events.INSTANCE_STOPPED, 0, True),
            (Events.SYSTEM_CREATED, 1, True),
            (Events.SYSTEM_UPDATED, 1, True),
            (Events.SYSTEM_REMOVED, 0, True),
            (Events.QUEUE_CLEARED, 0, False),
            (Events.ALL_QUEUES_CLEARED, 0, False),
            (Events.DB_CREATE, 0, False),
            (Events.DB_UPDATE, 0, False),
            (Events.DB_DELETE, 0, False),
            (Events.GARDEN_CREATED, 1, False),
            (Events.GARDEN_CONFIGURED, 2, False),
            (Events.GARDEN_UPDATED, 2, False),
            (Events.GARDEN_REMOVED, 2, False),
            (Events.FILE_CREATED, 0, False),
            (Events.GARDEN_STARTED, 1, False),
            (Events.GARDEN_STOPPED, 2, False),
            (Events.GARDEN_UNREACHABLE, 1, False),
            (Events.GARDEN_ERROR, 1, False),
            (Events.GARDEN_NOT_CONFIGURED, 1, False),
            (Events.GARDEN_SYNC, 2, False),
            (Events.ENTRY_STARTED, 0, False),
            (Events.ENTRY_STOPPED, 0, False),
            (Events.JOB_CREATED, 0, False),
            (Events.JOB_DELETED, 0, False),
            (Events.JOB_PAUSED, 0, False),
            (Events.JOB_RESUMED, 0, False),
            (Events.PLUGIN_LOGGER_FILE_CHANGE, 0, False),
            (Events.RUNNER_STARTED, 0, False),
            (Events.RUNNER_STOPPED, 0, False),
            (Events.RUNNER_REMOVED, 0, False),
            (Events.JOB_UPDATED, 0, False),
            (Events.JOB_EXECUTED, 0, False),
            (Events.USER_UPDATED, 0, False),
            (Events.USERS_IMPORTED, 0, False),
            (Events.ROLE_UPDATED, 0, False),
            (Events.ROLE_DELETED, 0, False),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_SYNC, 0, False),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_REMOVE, 0, False),
            (Events.COMMAND_PUBLISHING_BLOCKLIST_UPDATE, 0, False),
            (Events.TOPIC_CREATED, 0, False),
            (Events.TOPIC_UPDATED, 0, False),
            (Events.TOPIC_REMOVED, 0, False),
            (Events.REPLICATION_CREATED, 0, False),
            (Events.REPLICATION_UPDATED, 0, False),
            (Events.DIRECTORY_FILE_CHANGE, 0, False),
        ],
    )
    def test_garden_remote_callbacks(
        self, monkeypatch, bg_event, event_name, expected_calls, trigger_event
    ):
        """Tests to ensure the expected number of Handlers are called for remote events"""

        bg_event.name = event_name.name
        bg_event.garden = "remotegarden"

        config._CONFIG["garden"] = {"name": "localgarden"}

        event_manager = FanoutProcessor(name="event manager")
        add_internal_events_handler(event_manager)

        assert len(event_manager._managed_processors) == 15

        queue_mock = Mock()
        append_mock = Mock()
        queue_mock.append = append_mock

        for processor in event_manager._managed_processors:
            if hasattr(processor, "_trigger_event"):
                assert processor._trigger_event is None

        for processor in event_manager._managed_processors:

            if hasattr(processor, "_queue"):
                monkeypatch.setattr(processor, "_queue", queue_mock)
            processor.put(bg_event)

        for processor in event_manager._managed_processors:
            if hasattr(processor, "_trigger_event"):
                if trigger_event:
                    assert processor._trigger_event is not None
                else:
                    assert processor._trigger_event is None

        assert append_mock.call_count == expected_calls

    def test_unique_events(self, bg_event):
        """Tests to ensure events are de-dupped"""

        config._CONFIG["events_handler"]["requests"]["unique_data"] = True

        create_event = deepcopy(bg_event)
        create_event.payload.status = "CREATED"

        update_event = deepcopy(bg_event)
        update_event.payload.status = "IN_PROGRESS"

        complete_event = deepcopy(bg_event)
        complete_event.payload.status = "SUCCESS"

        config._CONFIG["garden"] = {"name": bg_event.garden}

        event_manager = FanoutProcessor(name="event manager")
        add_internal_events_handler(event_manager)

        assert len(event_manager._managed_processors) == 15

        evaluated = False
        for processor in event_manager._managed_processors:

            if (
                hasattr(processor, "_handler_tag")
                and processor._handler_tag == "Requests"
            ):
                processor.put(create_event)
                processor.put(create_event)
                processor.put(create_event)
                assert len(processor._queue) == 1
                assert (
                    processor._data[next(iter(processor._data))].payload.status
                    == "CREATED"
                )

                processor.put(update_event)
                assert len(processor._queue) == 1
                assert (
                    processor._data[next(iter(processor._data))].payload.status
                    == "IN_PROGRESS"
                )

                processor.put(complete_event)
                assert len(processor._queue) == 1
                assert (
                    processor._data[next(iter(processor._data))].payload.status
                    == "SUCCESS"
                )

                processor.put(create_event)
                processor.put(update_event)
                assert len(processor._queue) == 1
                assert (
                    processor._data[next(iter(processor._data))].payload.status
                    == "SUCCESS"
                )

                evaluated = True

        assert evaluated

    @pytest.mark.parametrize(
        "disabled_event_handler",
        ["garden", "plugin", "requests", "system", "file"],
    )
    def test_disable_event_handlers(self, disabled_event_handler):
        """Tests to ensure that handlers can be disabled via configuration"""

        config._CONFIG["events_handler"][disabled_event_handler]["enabled"] = False

        event_manager = FanoutProcessor(name="event manager")
        add_internal_events_handler(event_manager)

        assert len(event_manager._managed_processors) == 14

        for processor in event_manager._managed_processors:
            if hasattr(processor, "_handler_tag"):
                assert processor._handler_tag != disabled_event_handler
