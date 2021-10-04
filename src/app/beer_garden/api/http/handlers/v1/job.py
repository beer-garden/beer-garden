# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser
from brewtils.schemas import JobExportInputSchema, JobSchema

from beer_garden.api.http.base_handler import BaseHandler


class JobAPI(BaseHandler):
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
    async def post(self):
        """
        ---
        summary: Schedule a list of Jobs from a list of job descriptions.
        description: |
          Given a list of jobs from /export/jobs, each will be scheduled to run
          on the intervals that are set in their trigger arguments.
        parameters:
          - name: jobs
            in: body
            description: The Jobs to create/schedule
            schema:
              type: array
              items:
                $ref: '#/definitions/JobImport'
        responses:
          201:
            description: All new jobs have been created
            schema:
              $ref: '#/definitions/JobExport'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        parsed_job_list = SchemaParser.parse_job(self.request_body, many=True)

        response = await self.client(
            Operation(operation_type="JOB_CREATE_MULTI", args=[parsed_job_list])
        )

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class JobExportAPI(BaseHandler):
    async def post(self):
        """
        ---
        summary: Exports a list of Jobs from a list of IDs.
        description: |
          Jobs will be scheduled from a provided list to run on the intervals
          set in their trigger arguments.
        parameters:
          - name: ids
            in: body
            description: A list of the Jobs IDs whose job definitions should be \
            exported. Omitting this parameter or providing an empty map will export \
            all jobs.
            schema:
              $ref: '#/definitions/JobExport'
        responses:
          201:
            description: A list of jobs has been exported.
            schema:
              type: array
              items:
                $ref: '#/definitions/JobImport'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Jobs
        """
        filter_params_dict = {}

        # self.request_body is designed to return a 400 on a completely absent body
        # but we want to return all jobs if that's the case
        if len(self.request.body) > 0:
            decoded_body_as_dict = self.request_body

            if len(decoded_body_as_dict) > 0:  # i.e. it has keys
                input_schema = JobExportInputSchema()
                validated_input_data_dict = input_schema.load(decoded_body_as_dict).data
                filter_params_dict["id__in"] = validated_input_data_dict["ids"]

        response_objects = await self.client(
            Operation(
                operation_type="JOB_READ_ALL",
                kwargs={"filter_params": filter_params_dict},
            ),
            serialize_kwargs={"return_raw": True},
        )
        response = SchemaParser.serialize(
            response_objects, to_string=True, schema_name="JobExportSchema"
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
