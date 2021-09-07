"""Integration tests for Job import and export."""
import copy
from operator import attrgetter
from time import sleep
from typing import Any, Callable, List, Optional, Tuple

import pytest
from brewtils import EasyClient  # type: ignore
from brewtils.models import IntervalTrigger, Job, RequestTemplate  # type: ignore

try:
    from helper import wait_for_response
    from helper.assertion import assert_successful_request, assert_validation_error
except ImportError:
    from ...helper import wait_for_response  # type: ignore # noqa: F401
    from ...helper.assertion import (  # type: ignore  # noqa: F401
        assert_successful_request,
        assert_validation_error,
    )


job_name_base = f"import_export_interval_test_{{}}"  # noqa
job_wait_length = "seconds"
job_wait_default = 300
reschedule_key = "reschedule_on_finish"
reschedule_val = True
request_comment_key = "comment"
job_config = [
    # (IntervalTriggers args, RequestTemplate args)
    #
    # this can be expanded to run more tests over different types of Jobs
    (
        {
            "weeks": 0,
            "days": 0,
            "hours": 0,
            "minutes": 0,
            job_wait_length: job_wait_default,
            reschedule_key: reschedule_val,
        },
        {
            "system": "echo",
            "system_version": "3.0.0.dev0",
            "instance_name": "default",
            "namespace": "default",
            "command": "say",
            "parameters": {"message": "hello", "loud": False},
            request_comment_key: job_name_base,
        },
    )
]


@pytest.fixture(params=job_config)
def system_spec(request):
    """Create trigger and request template from parameters."""
    params: Tuple[Any, ...] = request.param

    trigger_args = params[0]
    req_template_args = params[1]

    return IntervalTrigger(**trigger_args), RequestTemplate(**req_template_args)


# convenience functions because we'll be doing a lot of mapping over lists
name_getter: Callable[[Job], str] = attrgetter("name")
id_getter: Callable[[Job], str] = attrgetter("id")


@pytest.mark.usefixtures("easy_client")
class TestJobImportExport:
    """Test functionality of job export and job import."""

    easy_client: EasyClient

    def setup_method(self, method):
        """Make sure there are no Jobs scheduled before testing."""
        base_wait_time = 0.1  # seconds
        existing_jobs = self.easy_client.find_jobs()

        for job in existing_jobs:
            self.easy_client.remove_job(id_getter(job))

        # irritating as this is, the job removal is done by the scheduler, which does
        # not operate in real time
        sleep(base_wait_time * len(existing_jobs))

    def test_export_interval_jobs(self, system_spec):
        """Test Job export functionality."""
        export_job_count = 5
        trigger = system_spec[0]
        req_template = system_spec[1]

        jobs_to_be_created_on_bg = self.make_jobs(
            export_job_count, trigger, req_template
        )
        jobs_actually_on_beer_garden = self.find_jobs_on_bg_from_job_list(
            "name", self.create_jobs_on_bg(jobs_to_be_created_on_bg)
        )

        # extract the IDs and use them to export the jobs
        jobs_on_beer_garden_ids = list(map(id_getter, jobs_actually_on_beer_garden))
        jobs_exported_from_beergarden: List[Job] = self.easy_client.export_jobs(
            jobs_on_beer_garden_ids
        )

        # now verify all names match, indicating up to ids, they are all the same Jobs
        assert (
            set(map(name_getter, jobs_actually_on_beer_garden))
            >= set(map(name_getter, jobs_exported_from_beergarden))
            >= set(map(name_getter, jobs_actually_on_beer_garden))
        )
        assert (
            set(map(name_getter, jobs_to_be_created_on_bg))
            >= set(map(name_getter, jobs_exported_from_beergarden))
            >= set(map(name_getter, jobs_to_be_created_on_bg))
        )

    def test_import_interval_jobs(self, system_spec):
        """Test Job import functionality."""
        import_job_count = 5
        trigger = system_spec[0]
        req_template = system_spec[1]

        job_definition_list = self.make_jobs(import_job_count, trigger, req_template)
        job_definitions_imported_to_beergarden = self.easy_client.import_jobs(
            job_definition_list
        )

        # we know we've been returned a type that says the jobs are imported, but
        # we need the actual Jobs that were created, so we search for them on the server
        jobs_on_beer_garden = self.find_jobs_on_bg_from_id_list(
            job_definitions_imported_to_beergarden
        )

        # now that we have the Jobs that are actually on BG, verify they are the same
        # as those we imported (i.e. their names match)
        assert (
            set(map(name_getter, job_definition_list))
            >= set(map(name_getter, jobs_on_beer_garden))
            >= set(map(name_getter, job_definition_list))
        )

    def test_imported_jobs_assigned_next_run_time(self, system_spec):
        """Test the scheduler assigns a next run time to imported jobs."""
        import_job_count = 5
        scheduler_wait_time_base = 0.01  # brief pause
        trigger = system_spec[0]
        req_template = system_spec[1]

        job_definition_list = self.make_jobs(import_job_count, trigger, req_template)
        job_definitions_imported_to_beergarden = self.easy_client.import_jobs(
            job_definition_list
        )

        # wait for scheduler to do its thing
        sleep(scheduler_wait_time_base * import_job_count)

        jobs_on_beer_garden = self.find_jobs_on_bg_from_id_list(
            job_definitions_imported_to_beergarden
        )

        def _is_not_none(x: Optional[Any]):
            return x is not None

        assert all(
            map(_is_not_none, map(attrgetter("next_run_time"), jobs_on_beer_garden))
        )

    def create_jobs_on_bg(self, job_list: List[Job]):
        return list(map(self.easy_client.create_job, job_list))  # noqa

    def find_jobs_on_bg_from_job_list(
        self, field: str, job_list: List[Job]
    ) -> List[Job]:
        return list(
            map(
                lambda x: x[0],
                [
                    self.easy_client.find_jobs(**{field: job_attr})
                    for job_attr in map(attrgetter(field), job_list)
                ],
            )
        )

    def find_jobs_on_bg_from_id_list(self, job_id_list: List[str]) -> List[Job]:
        return list(
            map(
                lambda x: x[0],
                [self.easy_client.find_jobs(id=id_) for id_ in job_id_list],
            )
        )

    @classmethod
    def make_jobs(
        cls, count: int, trigger: IntervalTrigger, request_template: RequestTemplate
    ) -> List[Job]:
        return [
            cls.make_interval_job(idx + 1, trigger, request_template)
            for idx in range(count)
        ]

    @staticmethod
    def make_interval_job(
        idx: int, trigger: IntervalTrigger, request_template: RequestTemplate
    ) -> Job:
        """Create a Job from parameters."""
        request_template_commented = copy.deepcopy(request_template)

        request_template_commented.comment = (
            str.format(request_template.comment, str(idx)) + " Job"
        )

        return Job(
            name=str.format(job_name_base, str(idx)),
            trigger_type="interval",
            trigger=trigger,
            request_template=request_template_commented,
            status="RUNNING",
            coalesce=True,
            max_instances=1,
        )
