# -*- coding: utf-8 -*-
from brewtils.errors import ModelValidationError
from brewtils.models import PatchOperation
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler


class InstanceAPI(BaseHandler):
    @authenticated(permissions=[Permissions.INSTANCE_READ])
    async def get(self, instance_id):
        """
        ---
        summary: Retrieve a specific Instance
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
          - name: instance_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
        responses:
          200:
            description: Instance with the given ID
            schema:
              $ref: '#/definitions/Instance'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Instances
        """
        response = await self.client.get_instance(self.request.namespace, instance_id)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.INSTANCE_DELETE])
    async def delete(self, instance_id):
        """
        ---
        summary: Delete a specific Instance
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
          - name: instance_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
        responses:
          204:
            description: Instance has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Instances
        """
        await self.client.remove_instance(self.request.namespace, instance_id)

        self.set_status(204)

    @authenticated(permissions=[Permissions.INSTANCE_UPDATE])
    async def patch(self, instance_id):
        """
        ---
        summary: Partially update an Instance
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * initialize
          * start
          * stop
          * heartbeat

          ```JSON
          [
            { "operation": "" }
          ]
          ```
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
          - name: instance_id
            in: path
            required: true
            description: The ID of the Instance
            type: string
          - name: runner_id
            in: query
            required: false
            description: The ID of the Instance
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Instance
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Instance with the given ID
            schema:
              $ref: '#/definitions/Instance'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Instances
        """
        response = ""
        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "initialize":
                response = await self.client.initialize_instance(
                    self.request.namespace, instance_id
                )

            elif operation == "start":
                response = await self.client.start_instance(
                    self.request.namespace, instance_id
                )

            elif operation == "stop":
                response = await self.client.stop_instance(
                    self.request.namespace, instance_id
                )

            elif operation == "heartbeat":
                response = await self.client.update_instance_status(
                    self.request.namespace, instance_id, "RUNNING"
                )

            elif operation == "replace":
                if op.path.lower() == "/status":
                    response = await self.client.update_instance_status(
                        self.request.namespace, instance_id, op.value
                    )
                else:
                    raise ModelValidationError(f"Unsupported path '{op.path}'")
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
