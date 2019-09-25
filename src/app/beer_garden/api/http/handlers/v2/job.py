# -*- coding: utf-8 -*-

from brewtils.errors import ModelValidationError
from brewtils.schema_parser import SchemaParser
from brewtils.schemas import JobSchema

from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.api.http.client import ExecutorClient


class JobAPI(BaseHandler):
    @authenticated(permissions=[Permissions.JOB_READ])
    async def get(self, namespace, job_id):
        """
        ---
        summary: Retrieve a specific Job
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        async with ExecutorClient() as client:
            thrift_response = await client.getJob(namespace, job_id)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)

    @authenticated(permissions=[Permissions.JOB_UPDATE])
    async def patch(self, namespace, job_id):
        """
        ---
        summary: Pause/Resume a job
        description: |
          The body of the request needs to contain a set of instructions
          detailing the actions to take. Currently the only operation
          supported is `update` with `path` of `/status`.


          You can pause a job with:
          ```JSON
          {
            "operations": [
              { "operation": "update", "path": "/status", "value": "PAUSED" }
            ]
          }
          ```

          And resume it with:
          ```JSON
          {
            "operations": [
                { "operation": "update", "path": "/status", "value": "RUNNING" }
            ]
          }
          ```
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        operations = SchemaParser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        for op in operations:
            if op.operation == "update":
                if op.path == "/status":
                    if str(op.value).upper() == "PAUSED":
                        async with ExecutorClient() as client:
                            response = await client.pauseJob(namespace, job_id)
                    elif str(op.value).upper() == "RUNNING":
                        async with ExecutorClient() as client:
                            response = await client.resumeJob(namespace, job_id)
                    else:
                        raise ModelValidationError(
                            f"Unsupported status value '{op.value}'"
                        )
                else:
                    raise ModelValidationError(f"Unsupported path value '{op.path}'")
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.JOB_DELETE])
    async def delete(self, namespace, job_id):
        """
        ---
        summary: Delete a specific Job.
        description: Will remove a specific job. No further executions will occur.
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        async with ExecutorClient() as client:
            await client.removeJob(namespace, job_id)

        self.set_status(204)


class JobListAPI(BaseHandler):
    @authenticated(permissions=[Permissions.JOB_READ])
    async def get(self, namespace):
        """
        ---
        summary: Retrieve all Jobs.
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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

        async with ExecutorClient() as client:
            thrift_response = await client.getJobs(namespace, filter_params)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)

    @authenticated(permissions=[Permissions.JOB_CREATE])
    async def post(self, namespace):
        """
        ---
        summary: Schedules a Job to be run.
        description: |
          Given a job, it will be scheduled to run on the interval
          set in the trigger argument.
        parameters:
          - name: namespace
            in: path
            required: true
            description: The namespace
            type: string
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
        async with ExecutorClient() as client:
            response = await client.createJob(namespace, self.request.decoded_body)

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
