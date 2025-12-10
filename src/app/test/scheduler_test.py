# -*- coding: utf-8 -*-

import pytest
from brewtils.models import Event, Events, IntervalTrigger
from brewtils.models import Job as BrewtilsJob
from brewtils.models import RequestTemplate
from mock import Mock

import beer_garden
from beer_garden.db.mongo.models import Job
from beer_garden.scheduler import MixedScheduler, create_jobs, handle_event


class TestScheduler:
    @pytest.fixture(autouse=True)
    def drop(self):
        yield
        Job.drop_collection()

    @pytest.fixture
    def mock_sync_scheduler(self, monkeypatch):
        sync_scheduler_mock = Mock()
        monkeypatch.setattr(
            beer_garden.scheduler, "BackgroundScheduler", sync_scheduler_mock
        )

        class MockApplication(object):
            scheduler = None

        beer_garden.application = MockApplication()
        beer_garden.application.scheduler = MixedScheduler()

        beer_garden.application.scheduler.internal_scheduled_jobs = Mock()

    def test_create_jobs_does_not_create_invalid_jobs(self):
        valid_job = BrewtilsJob(
            name="valid_job",
            trigger_type="interval",
            trigger=IntervalTrigger(hours=1),
            request_template=RequestTemplate(
                system="testsystem",
                system_version="1.2.3",
                instance_name="default",
                command="testcommand",
            ),
        )
        invalid_job = BrewtilsJob(name="invalid_job")

        results = create_jobs([valid_job, invalid_job])

        assert len(results["created"]) == 1
        assert len(results["rejected"]) == 1
        assert len(Job.objects.all()) == 1

    def test_event_handler_entry_start(
        self, mock_sync_scheduler, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {
            "garden": {"name": "default"},
            "replication": {"enabled": False},
            "scheduler": {
                "max_workers": 1,
                "job_defaults": {"coalesce": True, "max_instances": 1},
            },
            "db": {
                "prune": {
                    "in_progress_request_expiration": -1,
                    "interval": -1,
                    "ttl": {
                        "action": -1,
                        "file": -1,
                        "info": -1,
                    },
                }
            },
        }

        event = Event(
            name=Events.ENTRY_STARTED.name,
            garden="default",
            metadata={"entry_point_type": "HTTP"},
        )

        set_failed_event_manager()
        handle_event(event)
        check_failed_event_manager()

        assert beer_garden.application.scheduler.running

    def test_event_handler_job_create(
        self, mock_sync_scheduler, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {
            "garden": {"name": "default"},
            "replication": {"enabled": False},
            "scheduler": {
                "max_workers": 1,
                "job_defaults": {"coalesce": True, "max_instances": 1},
            },
            "db": {
                "prune": {
                    "in_progress_request_expiration": -1,
                    "interval": -1,
                    "ttl": {
                        "action": -1,
                        "file": -1,
                        "info": -1,
                    },
                }
            },
        }

        beer_garden.application.scheduler.start()

        valid_job = BrewtilsJob(
            name="valid_job",
            trigger_type="interval",
            trigger=IntervalTrigger(hours=1),
            request_template=RequestTemplate(
                system="testsystem",
                system_version="1.2.3",
                instance_name="default",
                command="testcommand",
            ),
        )

        results = create_jobs([valid_job])

        test_job = results["created"][0]

        test_job.status = "PAUSED"

        event = Event(
            name=Events.JOB_CREATED.name,
            garden="default",
            payload=test_job,
        )

        set_failed_event_manager()
        handle_event(event)
        check_failed_event_manager()

        assert beer_garden.application.scheduler._sync_scheduler.add_job.call_count == 1

    def test_event_handler_job_pause(
        self, mock_sync_scheduler, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {
            "garden": {"name": "default"},
            "replication": {"enabled": False},
            "scheduler": {
                "max_workers": 1,
                "job_defaults": {"coalesce": True, "max_instances": 1},
            },
            "db": {
                "prune": {
                    "in_progress_request_expiration": -1,
                    "interval": -1,
                    "ttl": {
                        "action": -1,
                        "file": -1,
                        "info": -1,
                    },
                }
            },
        }

        beer_garden.application.scheduler.start()

        valid_job = BrewtilsJob(
            name="valid_job",
            trigger_type="interval",
            trigger=IntervalTrigger(hours=1),
            request_template=RequestTemplate(
                system="testsystem",
                system_version="1.2.3",
                instance_name="default",
                command="testcommand",
            ),
        )

        results = create_jobs([valid_job])

        test_job = results["created"][0]

        test_job.status = "PAUSED"

        event = Event(
            name=Events.JOB_PAUSED.name,
            garden="default",
            payload=test_job,
        )

        set_failed_event_manager()
        handle_event(event)
        check_failed_event_manager()

        assert (
            beer_garden.application.scheduler._sync_scheduler.pause_job.call_count == 1
        )

    def test_event_handler_job_resume(
        self, mock_sync_scheduler, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {
            "garden": {"name": "default"},
            "replication": {"enabled": False},
            "scheduler": {
                "max_workers": 1,
                "job_defaults": {"coalesce": True, "max_instances": 1},
            },
            "db": {
                "prune": {
                    "in_progress_request_expiration": -1,
                    "interval": -1,
                    "ttl": {
                        "action": -1,
                        "file": -1,
                        "info": -1,
                    },
                }
            },
        }

        beer_garden.application.scheduler.start()

        valid_job = BrewtilsJob(
            name="valid_job",
            trigger_type="interval",
            trigger=IntervalTrigger(hours=1),
            request_template=RequestTemplate(
                system="testsystem",
                system_version="1.2.3",
                instance_name="default",
                command="testcommand",
            ),
        )

        results = create_jobs([valid_job])

        test_job = results["created"][0]

        test_job.status = "PAUSED"

        event = Event(
            name=Events.JOB_RESUMED.name,
            garden="default",
            payload=test_job,
        )

        set_failed_event_manager()
        handle_event(event)
        check_failed_event_manager()

        assert (
            beer_garden.application.scheduler._sync_scheduler.resume_job.call_count == 1
        )

    def test_event_handler_job_remove(
        self, mock_sync_scheduler, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {
            "garden": {"name": "default"},
            "replication": {"enabled": False},
            "scheduler": {
                "max_workers": 1,
                "job_defaults": {"coalesce": True, "max_instances": 1},
            },
            "db": {
                "prune": {
                    "in_progress_request_expiration": -1,
                    "interval": -1,
                    "ttl": {
                        "action": -1,
                        "file": -1,
                        "info": -1,
                    },
                }
            },
        }

        beer_garden.application.scheduler.start()

        valid_job = BrewtilsJob(
            name="valid_job",
            trigger_type="interval",
            trigger=IntervalTrigger(hours=1),
            request_template=RequestTemplate(
                system="testsystem",
                system_version="1.2.3",
                instance_name="default",
                command="testcommand",
            ),
        )

        results = create_jobs([valid_job])

        test_job = results["created"][0]

        test_job.status = "PAUSED"

        event = Event(
            name=Events.JOB_DELETED.name,
            garden="default",
            payload=test_job,
        )

        set_failed_event_manager()
        handle_event(event)
        check_failed_event_manager()

        assert (
            beer_garden.application.scheduler._sync_scheduler.remove_job.call_count == 1
        )

    def test_event_handler_job_execute(
        self, mock_sync_scheduler, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {
            "garden": {"name": "default"},
            "replication": {"enabled": False},
            "scheduler": {
                "max_workers": 1,
                "job_defaults": {"coalesce": True, "max_instances": 1},
            },
            "db": {
                "prune": {
                    "in_progress_request_expiration": -1,
                    "interval": -1,
                    "ttl": {
                        "action": -1,
                        "file": -1,
                        "info": -1,
                    },
                }
            },
        }

        beer_garden.application.scheduler.start()

        valid_job = BrewtilsJob(
            name="valid_job",
            trigger_type="interval",
            trigger=IntervalTrigger(hours=1),
            request_template=RequestTemplate(
                system="testsystem",
                system_version="1.2.3",
                instance_name="default",
                command="testcommand",
            ),
        )

        results = create_jobs([valid_job])

        test_job = results["created"][0]
        test_job.reset_interval = False
        test_job.status = "PAUSED"

        event = Event(
            name=Events.JOB_EXECUTED.name,
            garden="default",
            payload=test_job,
        )

        set_failed_event_manager()
        handle_event(event)
        check_failed_event_manager()

        assert beer_garden.application.scheduler._sync_scheduler.add_job.call_count == 1

    def test_event_handler_file_change(
        self, mock_sync_scheduler, set_failed_event_manager, check_failed_event_manager
    ):
        beer_garden.config._CONFIG = {
            "garden": {"name": "default"},
            "replication": {"enabled": False},
            "scheduler": {
                "max_workers": 1,
                "job_defaults": {"coalesce": True, "max_instances": 1},
            },
            "db": {
                "prune": {
                    "in_progress_request_expiration": -1,
                    "interval": -1,
                    "ttl": {
                        "action": -1,
                        "file": -1,
                        "info": -1,
                    },
                }
            },
        }

        beer_garden.application.scheduler.start()

        valid_job = BrewtilsJob(
            name="valid_job",
            trigger_type="interval",
            trigger=IntervalTrigger(hours=1),
            request_template=RequestTemplate(
                system="testsystem",
                system_version="1.2.3",
                instance_name="default",
                command="testcommand",
            ),
        )

        results = create_jobs([valid_job])

        test_job = results["created"][0]

        test_job.status = "PAUSED"
        test_job.reset_interval = False

        event = Event(
            name=Events.DIRECTORY_FILE_CHANGE.name,
            garden="default",
            payload=test_job,
            metadata={"src_path": "test/"},
        )

        set_failed_event_manager()
        handle_event(event)
        check_failed_event_manager()

        assert beer_garden.application.scheduler._sync_scheduler.add_job.call_count == 1
