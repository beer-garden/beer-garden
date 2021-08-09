# -*- coding: utf-8 -*-
from typing import Optional, Awaitable, List, Dict, Any

from brewtils.errors import ModelValidationError
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser
from brewtils.schemas import JobSchema

from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler


class JobAPI(BaseHandler):
    @authenticated(permissions=[Permissions.READ])
    async def get(self, job_id):
        """
        ---
        summary: Retrieve a specific Job
        parameters:
          - name: job_id
            in: path
            required: true
            description: The ID of the Job
            type: string
        responses:
          200:
            description: Job with the given ID
            schema:
              $ref: '#/definitions/Job'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """

        response = await self.client(
            Operation(operation_type="JOB_READ", args=[job_id])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.UPDATE])
    async def patch(self, job_id):
        """
        ---
        summary: Pause/Resume a job
        description: |
          The body of the request needs to contain a set of instructions
          detailing the actions to take. Currently the only operation
          supported is `update` with `path` of `/status`.


          You can pause a job with:
          ```JSON
          { "operation": "update", "path": "/status", "value": "PAUSED" }
          ```

          And resume it with:
          ```JSON
          { "operation": "update", "path": "/status", "value": "RUNNING" }
          ```
        parameters:
          - name: job_id
            in: path
            required: true
            description: The ID of the Job
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for the actions to take
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Job with the given ID
            schema:
              $ref: '#/definitions/Job'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            if op.operation == "update":
                if op.path == "/status":
                    if str(op.value).upper() == "PAUSED":
                        response = await self.client(
                            Operation(operation_type="JOB_PAUSE", args=[job_id])
                        )
                    elif str(op.value).upper() == "RUNNING":
                        response = await self.client(
                            Operation(operation_type="JOB_RESUME", args=[job_id])
                        )
                    else:
                        raise ModelValidationError(
                            f"Unsupported status value '{op.value}'"
                        )
                elif op.path == "/job":
                    response = await self.client(
                        Operation(
                            operation_type="JOB_UPDATE",
                            args=[SchemaParser.parse_job(op.value)],
                        )
                    )
                else:
                    raise ModelValidationError(f"Unsupported path value '{op.path}'")
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.DELETE])
    async def delete(self, job_id):
        """
        ---
        summary: Delete a specific Job.
        description: Will remove a specific job. No further executions will occur.
        parameters:
          - name: job_id
            in: path
            required: true
            description: The ID of the Job
            type: string
        responses:
          204:
            description: Job has been successfully deleted.
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """

        await self.client(Operation(operation_type="JOB_DELETE", args=[job_id]))

        self.set_status(204)


class JobListAPI(BaseHandler):
    @authenticated(permissions=[Permissions.READ])
    async def get(self):
        """
        ---
        summary: Retrieve all Jobs.
        responses:
          200:
            description: Successfully retrieved all systems.
            schema:
              type: array
              items:
                $ref: '#/definitions/Job'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        filter_params = {}
        for key in self.request.arguments.keys():
            if key in JobSchema.get_attribute_names():
                filter_params[key] = self.get_query_argument(key)

        response = await self.client(
            Operation(
                operation_type="JOB_READ_ALL", kwargs={"filter_params": filter_params}
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.CREATE])
    async def post(self):
        """
        ---
        summary: Schedules a Job to be run.
        description: |
          Given a job, it will be scheduled to run on the interval
          set in the trigger argument.
        parameters:
          - name: job
            in: body
            description: The Job to create/schedule
            schema:
              $ref: '#/definitions/Job'
        responses:
          201:
            description: A new job has been created
            schema:
              $ref: '#/definitions/Job'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """

        response = await self.client(
            Operation(
                operation_type="JOB_CREATE",
                args=[
                    SchemaParser.parse_job(
                        self.request.body.decode("utf-8"), from_string=True
                    )
                ],
            )
        )

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class JobImportAPI(BaseHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        return super().data_received(chunk)

    @authenticated(permissions=[Permissions.CREATE])
    async def post(self):
        """
        ---
        summary: Schedule a list of Jobs from a list of job descriptions.
        description: |
          Given a list of jobs from /export/jobs, each will be scheduled to run
          on the intervals set in their trigger arguments.
        parameters:
          - name: jobs
            in: body
            description: The Jobs to create/schedule
            schema:
              $ref: '#/definitions/JobExport'
        responses:
          201:
            description: All new jobs have been created
            schema:
              $ref: '#/definitions/JobImport'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        pass


class JobExportAPI(BaseHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        return super().data_received(chunk)

    @authenticated(permissions=[Permissions.CREATE])
    async def post(self):
        """
        ---
        summary: Exports a list of Jobs from a list of IDs.
        description: |
          Jobs will be scheduled from a provided list to run on the intervals
          set in their trigger arguments.
        parameters:
          - name: jobs
            in: body
            description: A list of the Jobs IDs whose job definitions should be \
            exported. Omitting this parameter will export all jobs.
            schema:
              $ref: '#/definitions/JobImport'
        responses:
          201:
            description: A list of jobs has been exported.
            schema:
              $ref: '#/definitions/JobExport'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        filter_params_dict = {}

        # we're focused on the "ids" list, but if other keys and values
        # are present in the body and/or if arguments are passed, allow
        # them through; that is, provide maximum flexibility to the user
        for key in self.request.arguments:
            if key in JobSchema.get_attribute_names():
                filter_params_dict[key] = self.get_query_argument(key)

        decoded_body = self.request.body.decode("utf-8")

        if len(decoded_body):
            ids_string = "ids"
            arg_dict: Dict[str, Any] = SchemaParser.parse_job_ids(
                decoded_body, from_string=True
            )

            if ids_string not in arg_dict:
                raise ValueError(f"JSON body did not include '{ids_string}' key")

            ids = arg_dict[ids_string]
            assert isinstance(ids, list)

            filter_params_dict["id__in"] = ids

            for key, val in arg_dict.items():
                if key != ids_string:
                    filter_params_dict[key] = val

        response = await self.client(
            Operation(
                operation_type="JOB_READ_ALL",
                kwargs={"filter_params": filter_params_dict},
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
