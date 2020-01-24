# -*- coding: utf-8 -*-
import json

import beer_garden
from beer_garden.router import Route_Type, Route_Class
from brewtils.errors import ModelValidationError
from brewtils.schema_parser import SchemaParser
from brewtils.schemas import JobSchema

from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler


class JobAPI(BaseHandler):
    @authenticated(permissions=[Permissions.JOB_READ])
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
            obj_id=job_id, route_class=Route_Class.JOB, route_type=Route_Type.READ
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.JOB_UPDATE])
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

        response = await self.client(
            obj_id=job_id,
            brewtils_obj=SchemaParser.parse_patch(
                self.request.decoded_body, from_string=True
            ),
            route_class=Route_Class.JOB,
            route_type=Route_Type.UPDATE,
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.JOB_DELETE])
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

        await self.client(
            obj_id=job_id, route_class=Route_Class.JOB, route_type=Route_Type.DELETE
        )

        self.set_status(204)


class JobListAPI(BaseHandler):
    @authenticated(permissions=[Permissions.JOB_READ])
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
            route_class=Route_Class.JOB,
            route_type=Route_Type.READ,
            filter_params=filter_params,
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.JOB_CREATE])
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
            brewtils_obj=SchemaParser.parse_job(
                self.request.decoded_body, from_string=True
            ),
            route_class=Route_Class.JOB,
            route_type=Route_Type.CREATE,
        )

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
