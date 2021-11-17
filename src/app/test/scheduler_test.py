# -*- coding: utf-8 -*-

import pytest
from brewtils.models import IntervalTrigger
from brewtils.models import Job as BrewtilsJob
from brewtils.models import RequestTemplate

from beer_garden.db.mongo.models import Job
from beer_garden.scheduler import create_jobs


class TestScheduler:
    @pytest.fixture(autouse=True)
    def drop(self):
        yield
        Job.drop_collection()

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
