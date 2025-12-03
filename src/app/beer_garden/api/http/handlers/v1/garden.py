# -*- coding: utf-8 -*-
import logging

from brewtils.errors import ModelValidationError
from brewtils.models import Garden, Operation, Permissions
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.api.http.schemas.v1.garden import GardenRemoveStatusInfoSchema
from beer_garden.garden import local_garden

logger = logging.getLogger(__name__)


def _remove_heartbeat_history(response: str, many: bool = False) -> str:
    """Strips out the status_info.history models

    This balloons out the size of the returned object, and isn't currently
    required for the UI for display purposes, so we are clearing the list
    """
    if response == "" or response == "null":
        return response
    system_data = GardenRemoveStatusInfoSchema(many=many).loads(response).data
    return GardenRemoveStatusInfoSchema(many=many).dumps(system_data).data


class GardenAPI(AuthorizationHandler):

    async def get(self, garden_name):
        """
        ---
        summary: Retrieve a specific Garden
        parameters:
          - name: garden_name
            in: path
            required: true
            description: Read specific Garden Information
            type: string
          - name: include_fields
            in: query
            required: false
            description: Specify fields to include in the response. All other
              fields will be excluded.
            type: array
            collectionFormat: csv
            items:
              type: string
          - name: exclude_fields
            in: query
            required: false
            description: Specify fields to exclude from the response
            type: array
            collectionFormat: csv
            items:
              type: string
        responses:
          200:
            description: Garden with the given garden_name
            schema:
              $ref: '#/definitions/Garden'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Garden
        """

        include_fields = self.get_query_argument("include_fields", None)
        if include_fields:
            include_fields = set(include_fields.split(","))

        exclude_fields = self.get_query_argument("exclude_fields", None)
        if exclude_fields:
            exclude_fields = set(exclude_fields.split(","))

        response = await self.process_operation(
            Operation(
                operation_type="GARDEN_READ",
                args=[garden_name],
                kwargs={
                    "include_fields": include_fields,
                    "exclude_fields": exclude_fields,
                },
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(_remove_heartbeat_history(response))

    async def delete(self, garden_name):
        """
        ---
        summary: Delete a specific Garden
        parameters:
          - name: garden_name
            in: path
            required: true
            description: Garden to use
            type: string
        responses:
          204:
            description: Garden has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Garden
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        garden = self.get_or_raise(Garden, name=garden_name)

        await self.process_operation(
            Operation(operation_type="GARDEN_DELETE", args=[garden.name])
        )

        self.set_status(204)

    async def patch(self, garden_name):
        """
        ---
        summary: Partially update a Garden
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * initializing
          * running
          * stopped
          * block
          * update

          ```JSON
          [
            { "operation": "" }
          ]
          ```
        parameters:
          - name: garden_name
            in: path
            required: true
            description: Garden to use
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Garden
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Garden with the given garden_name
            schema:
              $ref: '#/definitions/Garden'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Garden
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        garden = self.get_or_raise(Garden, name=garden_name)

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation in ["initializing", "running", "stopped", "block"]:
                response = await self.process_operation(
                    Operation(
                        operation_type="GARDEN_UPDATE_STATUS",
                        args=[garden.name, operation.upper()],
                    )
                )
            elif operation == "heartbeat":
                response = await self.process_operation(
                    Operation(
                        operation_type="GARDEN_UPDATE_STATUS",
                        args=[garden.name, "RUNNING"],
                    )
                )
            elif operation == "connection":
                connection_type = op.value.get("connection_type")
                status = op.value.get("status")
                api = op.value.get("api")

                if connection_type.upper() == "PUBLISHING":
                    response = await self.process_operation(
                        Operation(
                            operation_type="GARDEN_UPDATE_PUBLISHING_STATUS",
                            kwargs={"garden_name": garden.name, "api": api},
                            args=[status],
                        )
                    )
                elif connection_type.upper() == "RECEIVING":
                    response = await self.process_operation(
                        Operation(
                            operation_type="GARDEN_UPDATE_RECEIVING_STATUS",
                            kwargs={"garden_name": garden.name, "api": api},
                            args=[status],
                        )
                    )

            elif operation == "sync":
                response = await self.process_operation(
                    Operation(
                        operation_type="GARDEN_SYNC",
                        kwargs={"sync_target": garden.name},
                    )
                )

            elif operation == "sync_users":
                response = await self.process_operation(
                    Operation(
                        operation_type="USER_SYNC_GARDEN",
                        kwargs={"garden_name": garden.name},
                    )
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(_remove_heartbeat_history(response))


class GardenListAPI(AuthorizationHandler):

    async def get(self):
        """
        ---
        summary: Retrieve a list of Gardens
        parameters:
          - name: include_fields
            in: query
            required: false
            description: Specify fields to include in the response. All other
              fields will be excluded.
            type: array
            collectionFormat: csv
            items:
              type: string
          - name: exclude_fields
            in: query
            required: false
            description: Specify fields to exclude from the response
            type: array
            collectionFormat: csv
            items:
              type: string
        responses:
          200:
            description: A list of all gardens
            schema:
              type: array
              items:
                $ref: '#/definitions/Garden'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Garden
        """

        include_fields = self.get_query_argument("include_fields", None)
        if include_fields:
            include_fields = set(include_fields.split(","))

        exclude_fields = self.get_query_argument("exclude_fields", None)
        if exclude_fields:
            exclude_fields = set(exclude_fields.split(","))

        permitted_gardens_list = await self.process_operation(
            Operation(
                operation_type="GARDEN_READ_ALL",
                kwargs={
                    "include_fields": include_fields,
                    "exclude_fields": exclude_fields,
                },
            )
        )
        self.write(_remove_heartbeat_history(permitted_gardens_list, many=True))

    async def post(self):
        """
        ---
        summary: Create a new Garden
        parameters:
          - name: garden
            in: body
            description: The Garden definition to create
            schema:
              $ref: '#/definitions/Garden'
        responses:
          201:
            description: A new Garden has been created
            schema:
              $ref: '#/definitions/Garden'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Garden
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        garden = SchemaParser.parse_garden(self.request.decoded_body, from_string=True)

        self.verify_user_permission_for_object(garden)

        response = await self.process_operation(
            Operation(
                operation_type="GARDEN_CREATE",
                args=[garden],
            )
        )

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(_remove_heartbeat_history(response))

    async def patch(self):
        """
        ---
        summary: Partially update a Garden
        description: |
          The body of the request needs to contain a set of instructions detailing the
          updates to apply. Currently the only operations are:

          * sync
          * sync_users

          ```JSON
          [
            { "operation": "" }
          ]
          ```
        parameters:
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Garden
            schema:
              $ref: '#/definitions/Patch'
        responses:
          204:
            description: Patch operation has been successfully forwarded
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Garden
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_permission_for_object(local_garden())

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "rescan":
                await self.process_operation(
                    Operation(
                        operation_type="GARDEN_RESCAN",
                        kwargs={"sync_gardens": True},
                    )
                )

            elif operation == "sync":
                await self.process_operation(
                    Operation(
                        operation_type="GARDEN_SYNC",
                    )
                )

            elif operation == "sync_users":
                await self.process_operation(
                    Operation(
                        operation_type="USER_SYNC",
                    )
                )
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_status(204)
