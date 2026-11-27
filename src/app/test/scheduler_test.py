# -*- coding: utf-8 -*-

import pytest
from brewtils.errors import ModelValidationError
from brewtils.models import DateTrigger, IntervalTrigger
from brewtils.models import Job as BrewtilsJob
from brewtils.models import RequestTemplate

from beer_garden.db.mongo.models import Job
from beer_garden.scheduler import clean_job, create_jobs


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

    def test_invalid_trigger_type(self):
        with pytest.raises(ModelValidationError):
            clean_job(Job(trigger_type="INVALID_TRIGGER_TYPE"))

    def test_trigger_mismatch(self):
        date_trigger = DateTrigger()
        with pytest.raises(ModelValidationError):
            clean_job(Job(trigger_type="cron", trigger=date_trigger))
