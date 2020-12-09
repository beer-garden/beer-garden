# -*- coding: utf-8 -*-
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.authorization import Permissions, authenticated
from beer_garden.api.http.base_handler import BaseHandler


class RunnerAPI(BaseHandler):

    parser = SchemaParser()

    @authenticated(permissions=[Permissions.DELETE])
    async def delete(self, runner_id):
        """
        ---
        summary: Delete a runner
        parameters:
          - name: runner_id
            in: path
            required: true
            description: The ID of the Runner
            type: string
        responses:
          200:
            description: List of runner states
            schema:
              $ref: '#/definitions/Job'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Runners
        """

        response = await self.client(
            Operation(operation_type="RUNNER_DELETE", args=[runner_id])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class RunnerListAPI(BaseHandler):

    parser = SchemaParser()

    @authenticated(permissions=[Permissions.READ])
    async def get(self):
        """
        ---
        summary: Retrieve runners
        responses:
          200:
            description: List of runner states
            schema:
              $ref: '#/definitions/Job'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Runners
        """

        response = await self.client(Operation(operation_type="RUNNER_STATE_READ"))

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
