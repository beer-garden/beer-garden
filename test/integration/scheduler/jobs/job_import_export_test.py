"""TODO."""
import copy
from operator import attrgetter
from typing import Any, Callable, Tuple, Optional

import pytest
from brewtils import EasyClient  # type: ignore
from brewtils.models import (  # type: ignore
    IntervalTrigger,
    Job,
    JobDefinitionList,
    JobIDList,
    RequestTemplate,
)

# TODO: understand when the try block will succeed and when the except
# TODO: block will execute; i.e. find out why this pattern is necessary
try:
    from helper import wait_for_response
    from helper.assertion import assert_successful_request, assert_validation_error
except ImportError:
    from ...helper import wait_for_response  # type: ignore # noqa: F401
    from ...helper.assertion import (  # type: ignore  # noqa: F401
        assert_successful_request,
        assert_validation_error,
    )


job_name_base = f"import_export_interval_test_{{}}"
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


# convenience function because we'll be doing a lot of mapping over lists
def _is_not_none(x: Optional[Any]):
    return x is not None


@pytest.mark.usefixtures("easy_client")
class TestJobImportExport:
    """Test functionality of job export and job import.

    NOTE: These tests perform a lot of checking of types, lengths of lists, etc. that
    would be more appropriate in unit tests. Once we have figured out how to run unit
    tests, many of the asserts can be removed."""

    easy_client: EasyClient

    def test_export_interval_jobs(self, system_spec):
        """Test Job export functionality."""
        export_job_count = 5
        name_getter: Callable[[Job], str] = attrgetter("name")
        id_getter: Callable[[Job], str] = attrgetter("id")

        trigger = system_spec[0]
        req_template = system_spec[1]

        jobs_to_be_created = [
            self.create_interval_job(idx + 1, trigger, req_template)
            for idx in range(export_job_count)
        ]
        job_creation_responses = list(
            map(self.easy_client.create_job, jobs_to_be_created)
        )

        # test that none of the responses are 'None' and we have the right count
        assert all(map(_is_not_none, job_creation_responses))
        assert len(job_creation_responses) == export_job_count

        jobs_on_beer_garden = [
            self.easy_client.find_jobs(name=job_name)
            for job_name in map(name_getter, jobs_to_be_created)
        ]

        # test that all the returns are not 'None' and are lists of the expected length
        # and type
        assert (
            isinstance(jobs_on_beer_garden, list)
            and len(jobs_on_beer_garden) == export_job_count
        )
        assert all(map(_is_not_none, jobs_on_beer_garden))
        assert all(map(lambda x: isinstance(x, list), jobs_on_beer_garden))
        assert all(map(lambda x: len(x) == 1, jobs_on_beer_garden))

        # we lift them because they are lists, as we've verified
        jobs_on_beer_garden_lifted = list(map(lambda x: x[0], jobs_on_beer_garden))

        # test that the Jobs returned are actually Jobs
        assert all(map(_is_not_none, jobs_on_beer_garden_lifted))
        assert all(map(lambda x: isinstance(x, Job), jobs_on_beer_garden_lifted))

        # extract the IDs and use them to export the jobs
        jobs_on_beer_garden_ids = list(map(id_getter, jobs_on_beer_garden_lifted))
        job_id_list_for_export = JobIDList(jobs_on_beer_garden_ids)
        jobs_exported_from_beergarden: JobDefinitionList = self.easy_client.export_jobs(
            job_id_list_for_export
        )

        assert isinstance(jobs_exported_from_beergarden, JobDefinitionList)

        exported_jobs = jobs_exported_from_beergarden.jobs

        # check that the Jobs we got back are as we expect
        assert (
            isinstance(exported_jobs, list) and len(exported_jobs) == export_job_count
        )
        assert all(map(lambda x: isinstance(x, Job), exported_jobs))

        # now verify all names match, indicating up to ids, they are all the same Jobs
        assert (
            set(map(name_getter, jobs_on_beer_garden_lifted))
            >= set(map(name_getter, exported_jobs))
            >= set(map(name_getter, jobs_on_beer_garden_lifted))
        )
        assert (
            set(map(name_getter, jobs_to_be_created))
            >= set(map(name_getter, exported_jobs))
            >= set(map(name_getter, jobs_to_be_created))
        )
        assert (
            set(map(name_getter, jobs_on_beer_garden_lifted))
            >= set(map(name_getter, jobs_to_be_created))
            >= set(map(name_getter, jobs_on_beer_garden_lifted))
        )

    def test_import_interval_jobs(self, system_spec):
        """Test Job import functionality."""
        import_job_count = 5
        name_getter: Callable[[Job], str] = attrgetter("name")

        trigger = system_spec[0]
        req_template = system_spec[1]

        base_jobs_list = [
            self.create_interval_job(idx, trigger, req_template)
            for idx in range(import_job_count)
        ]
        job_definition_list = JobDefinitionList(jobs=base_jobs_list)
        job_definitions_imported_to_beergarden = self.easy_client.import_jobs(
            job_definition_list
        )

        assert isinstance(job_definitions_imported_to_beergarden, JobIDList)
        assert len(job_definitions_imported_to_beergarden.ids) == import_job_count

        # we know we've been returned a type that says the jobs are imported, but
        # we need the actual Jobs that were created, so we search for them on the server
        jobs_on_beer_garden = [
            self.easy_client.find_jobs(name=job_name)
            for job_name in map(name_getter, base_jobs_list)
        ]

        # lift them because they're lists
        assert all(map(lambda x: isinstance(x, list), jobs_on_beer_garden))

        jobs_on_beer_garden_lifted = list(map(lambda x: x[0], jobs_on_beer_garden))

        assert all(
            map(
                lambda x: x is not None and isinstance(x, Job),
                jobs_on_beer_garden_lifted,
            )
        )

        # now that we have the Jobs that are actually on BG, verify they are the same
        # as those we imported (i.e. their names match)
        assert (
            set(map(name_getter, base_jobs_list))
            >= set(map(name_getter, jobs_on_beer_garden_lifted))
            >= set(map(name_getter, base_jobs_list))
        )

    @staticmethod
    def create_interval_job(
        idx: int, trigger: IntervalTrigger, request_template: RequestTemplate
    ):
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
