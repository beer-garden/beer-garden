# -*- coding: utf-8 -*-
from collections import deque
from copy import deepcopy

import pytest
from brewtils.models import Events, Request

from beer_garden import config
from beer_garden.events.handlers import add_internal_events_handler
from beer_garden.events.processors import FanoutProcessor


class TestHandlers:

    def run_event_handler_test(self, event, target_handlers, monkeypatch):

        config._CONFIG["garden"] = {"name": "localgarden"}

        event_manager = FanoutProcessor(name="event manager")
        add_internal_events_handler(event_manager)

        assert len(event_manager._managed_processors) == 14

        for processor in event_manager._managed_processors:

            if hasattr(processor, "_queue"):
                if processor._name in target_handlers:

                    processor.clear()
                    processor.put(event)
                    queue_depth = (
                        len(processor._queue)
                        if isinstance(processor._queue, deque)
                        else processor._queue.qsize()
                    )
                    if processor._name in target_handlers:
                        assert queue_depth == 1
                    else:
                        assert queue_depth == 0

    @pytest.mark.parametrize(
        "event_name",
        [
            Events.BREWVIEW_STARTED,
            Events.BREWVIEW_STOPPED,
            Events.BARTENDER_STARTED,
            Events.BARTENDER_STOPPED,
            Events.REQUEST_DELETED,
            Events.QUEUE_CLEARED,
            Events.ALL_QUEUES_CLEARED,
            Events.DB_CREATE,
            Events.DB_UPDATE,
            Events.DB_DELETE,
            Events.FILE_CREATED,
            Events.ENTRY_STOPPED,
            Events.RUNNER_STARTED,
            Events.RUNNER_STOPPED,
            Events.RUNNER_REMOVED,
            Events.USERS_IMPORTED,
            Events.ROLE_UPDATED,
            Events.COMMAND_PUBLISHING_BLOCKLIST_SYNC,
            Events.COMMAND_PUBLISHING_BLOCKLIST_REMOVE,
            Events.COMMAND_PUBLISHING_BLOCKLIST_UPDATE,
            Events.TOPIC_CREATED,
            Events.TOPIC_UPDATED,
            Events.TOPIC_REMOVED,
        ],
    )
    def test_noop_events(self, bg_event, event_name, monkeypatch):
        bg_event.name = event_name.name
        bg_event.garden = "localgarden"

        self.run_event_handler_test(bg_event, [], monkeypatch)

        bg_event.garden = "remotegaren"

        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_request_create_event(self, bg_event, bg_request, monkeypatch):
        bg_event.name = Events.REQUEST_CREATED.name
        bg_event.payload = bg_request
        bg_event.payload_type = "Request"
        bg_event.garden = "localgarden"
        bg_request.status = "CREATED"
        bg_event.payload.parameters["file_based"] = {
            "type": "chunk",
            "details": {"file_id": "123"},
        }

        self.run_event_handler_test(bg_event, ["File"], monkeypatch)
        bg_event.garden = "remotegaren"

        self.run_event_handler_test(bg_event, ["Requests"], monkeypatch)

    def test_request_in_progress_event(self, bg_event, bg_request, monkeypatch):
        bg_event.name = Events.REQUEST_STARTED.name
        bg_event.payload = bg_request
        bg_event.payload_type = "Request"
        bg_event.garden = "localgarden"
        bg_request.status = "IN_PROGRESS"

        self.run_event_handler_test(bg_event, [], monkeypatch)
        bg_event.garden = "remotegaren"

        self.run_event_handler_test(bg_event, ["Requests"], monkeypatch)

    def test_request_completed_event(self, bg_event, bg_request, monkeypatch):
        bg_event.name = Events.REQUEST_COMPLETED.name
        bg_event.payload = bg_request
        bg_event.payload_type = "Request"
        for success_status in Request.COMPLETED_STATUSES:
            bg_event.garden = "localgarden"
            bg_request.status = success_status

            self.run_event_handler_test(
                bg_event, ["Requests wait events", "Requests"], monkeypatch
            )
            bg_event.garden = "remotegaren"

            self.run_event_handler_test(bg_event, ["Requests"], monkeypatch)

    def test_request_canceled_event(self, bg_event, bg_request, monkeypatch):
        bg_event.name = Events.REQUEST_CANCELED.name
        bg_event.payload = bg_request
        bg_event.payload_type = "Request"

        bg_event.garden = "localgarden"
        bg_request.status = "CANCELED"

        self.run_event_handler_test(
            bg_event, ["Requests wait events", "Requests"], monkeypatch
        )
        bg_event.garden = "remotegaren"

        self.run_event_handler_test(bg_event, ["Requests"], monkeypatch)

    def test_request_updated_event(self, bg_event, bg_request, monkeypatch):
        bg_event.name = Events.REQUEST_UPDATED.name
        bg_event.payload = bg_request
        bg_event.payload_type = "Request"

        bg_event.garden = "localgarden"
        for success_status in Request.COMPLETED_STATUSES:
            bg_request.status = success_status
            self.run_event_handler_test(bg_event, [], monkeypatch)
            bg_event.garden = "remotegaren"
            self.run_event_handler_test(bg_event, ["Requests"], monkeypatch)

        bg_event.garden = "localgarden"
        bg_request.status = "IN_PROGRESS"
        self.run_event_handler_test(bg_event, [], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Requests"], monkeypatch)

        bg_event.garden = "localgarden"
        bg_request.status = "CREATED"
        self.run_event_handler_test(bg_event, [], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Requests"], monkeypatch)

    def test_request_topic_publish_event(self, bg_event, bg_request, monkeypatch):
        bg_event.name = Events.REQUEST_TOPIC_PUBLISH.name
        bg_event.payload = bg_request
        bg_event.payload_type = "Request"
        bg_event.metadata = {
            "topic": "topic",
            "propagate": False,
        }

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Publish Requests"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

        bg_event.metadata["propagate"] = True

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Publish Requests"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Publish Requests"], monkeypatch)

    def test_instance_initialized_event(self, bg_event, monkeypatch):
        bg_event.name = Events.INSTANCE_INITIALIZED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Local plugins manager"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_instance_started_event(self, bg_event, monkeypatch):
        bg_event.name = Events.INSTANCE_STARTED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, [], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_instance_updated_event(self, bg_event, monkeypatch):
        bg_event.name = Events.INSTANCE_UPDATED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Plugin"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_instance_stopped_event(self, bg_event, monkeypatch):
        bg_event.name = Events.INSTANCE_STOPPED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Local plugins manager"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_system_created_event(self, bg_event, monkeypatch):
        bg_event.name = Events.SYSTEM_CREATED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Router", "System"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Router"], monkeypatch)

    def test_system_updated_event(self, bg_event, monkeypatch):
        bg_event.name = Events.SYSTEM_UPDATED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Router", "System"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Router"], monkeypatch)

    def test_system_removed_event(self, bg_event, monkeypatch):
        bg_event.name = Events.SYSTEM_REMOVED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["System"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_garden_created_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_CREATED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)

    def test_garden_configured_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_CONFIGURED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Router", "Garden"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Router", "Garden"], monkeypatch)

    def test_garden_updated_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_UPDATED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Router", "Garden"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Router", "Garden"], monkeypatch)

    def test_garden_removed_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_REMOVED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Router", "Garden"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Router", "Garden"], monkeypatch)

    def test_garden_started_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_STARTED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)

    def test_garden_stopped_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_STOPPED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(
            bg_event, ["Requests wait events", "Garden"], monkeypatch
        )
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)

    def test_garden_unreachable_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_UNREACHABLE.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)

    def test_garden_error_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_ERROR.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)

    def test_garden_not_configured_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_NOT_CONFIGURED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)

    def test_garden_sync_event(self, bg_event, monkeypatch):
        bg_event.name = Events.GARDEN_SYNC.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Router", "Garden"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Router", "Garden"], monkeypatch)

    def test_entry_started_event(self, bg_event, monkeypatch):
        bg_event.name = Events.ENTRY_STARTED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(
            bg_event, ["Local plugins manager", "Garden"], monkeypatch
        )
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, ["Garden"], monkeypatch)

    def test_job_created_event(self, bg_event, bg_job, monkeypatch):
        bg_event.name = Events.JOB_CREATED.name
        bg_event.payload = bg_job
        bg_event.payload_type = "Job"

        bg_event.payload.request_template.parameters["file_based"] = {
            "type": "chunk",
            "details": {"file_id": "123"},
        }

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Scheduler", "File"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_job_deleted_event(self, bg_event, bg_job, monkeypatch):
        bg_event.name = Events.JOB_DELETED.name
        bg_event.payload = bg_job
        bg_event.payload_type = "Job"

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Scheduler"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_job_pause_event(self, bg_event, bg_job, monkeypatch):
        bg_event.name = Events.JOB_PAUSED.name
        bg_event.payload = bg_job
        bg_event.payload_type = "Job"

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Scheduler"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_job_resume_event(self, bg_event, bg_job, monkeypatch):
        bg_event.name = Events.JOB_RESUMED.name
        bg_event.payload = bg_job
        bg_event.payload_type = "Job"

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Scheduler"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_job_updated_event(self, bg_event, bg_job, monkeypatch):
        bg_event.name = Events.JOB_UPDATED.name
        bg_event.payload = bg_job
        bg_event.payload_type = "Job"

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Scheduler"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_job_executed_event(self, bg_event, bg_job, monkeypatch):
        bg_event.name = Events.JOB_EXECUTED.name
        bg_event.payload = bg_job
        bg_event.payload_type = "Job"

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Scheduler"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_plugin_logger_file_change_event(self, bg_event, monkeypatch):
        bg_event.name = Events.PLUGIN_LOGGER_FILE_CHANGE.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Log"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_user_updated_event(self, bg_event, monkeypatch):
        bg_event.name = Events.USER_UPDATED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["User event handler"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_role_deleted_event(self, bg_event, monkeypatch):
        bg_event.name = Events.ROLE_DELETED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["User event handler"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_replication_created_event(self, bg_event, monkeypatch):
        bg_event.name = Events.REPLICATION_CREATED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(
            bg_event, ["Replication event handler"], monkeypatch
        )
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_replication_updated_event(self, bg_event, monkeypatch):
        bg_event.name = Events.REPLICATION_UPDATED.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(
            bg_event, ["Replication event handler"], monkeypatch
        )
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_directory_file_event(self, bg_event, monkeypatch):
        bg_event.name = Events.DIRECTORY_FILE_CHANGE.name

        bg_event.garden = "localgarden"
        self.run_event_handler_test(bg_event, ["Scheduler"], monkeypatch)
        bg_event.garden = "remotegaren"
        self.run_event_handler_test(bg_event, [], monkeypatch)

    def test_unique_events(self, bg_event):
        """Tests to ensure events are de-dupped"""

        create_event = deepcopy(bg_event)
        create_event.payload.status = "CREATED"

        update_event = deepcopy(bg_event)
        update_event.payload.status = "IN_PROGRESS"

        complete_event = deepcopy(bg_event)
        complete_event.payload.status = "SUCCESS"

        config._CONFIG["garden"] = {"name": bg_event.garden}

        event_manager = FanoutProcessor(name="event manager")
        add_internal_events_handler(event_manager)

        assert len(event_manager._managed_processors) == 14

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
                assert len(processor._data) == 1
                assert (
                    processor._data[next(iter(processor._data))].payload.status
                    == "CREATED"
                )

                processor.put(update_event)
                assert len(processor._queue) == 1
                assert len(processor._data) == 1
                assert (
                    processor._data[next(iter(processor._data))].payload.status
                    == "IN_PROGRESS"
                )

                processor.put(complete_event)
                assert len(processor._queue) == 1
                assert len(processor._data) == 1
                assert (
                    processor._data[next(iter(processor._data))].payload.status
                    == "SUCCESS"
                )

                processor.put(create_event)
                processor.put(update_event)
                assert len(processor._queue) == 1
                assert len(processor._data) == 1
                assert (
                    processor._data[next(iter(processor._data))].payload.status
                    == "SUCCESS"
                )

                evaluated = True

        assert evaluated
