# -*- coding: utf-8 -*-
import logging

from brewtils.errors import ModelValidationError
from brewtils.models import Garden, Operation, Permissions
from brewtils.schema_parser import SchemaParser
from brewtils.schemas import GardenSchema as BrewtilsGardenSchema

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden

logger = logging.getLogger(__name__)


def _remove_heartbeat_history(response: str, many: bool = False) -> str:
    """Strips out the status_info.history models

    This balloons out the size of the returned object, and isn't currently
    required for the UI for display purposes, so we are clearing the list
    """

    if response == "" or response == "null":
        return response
    garden_data = BrewtilsGardenSchema(many=many).loads(response)

    if many:
        for garden in garden_data:
            _remove_garden_history(garden)

    return BrewtilsGardenSchema(
        many=many,
    ).dumps(_remove_garden_history(garden_data))


def _remove_status_info_history(value):
    if "status_info" in value and "history" in value["status_info"]:
        del value["status_info"]["history"]
    return value


def _remove_garden_history(garden: Garden):
    garden = _remove_status_info_history(garden)

    if "systems" in garden:
        for system in garden["systems"]:
            if "instances" in system:
                for instance in system["instances"]:
                    instance = _remove_status_info_history(instance)

    if "receiving_connections" in garden:
        for receiving_connection in garden["receiving_connections"]:
            receiving_connection = _remove_status_info_history(receiving_connection)

    if "publishing_connection" in garden:
        for publishing_connection in garden["publishing_connections"]:
            publishing_connection = _remove_status_info_history(publishing_connection)

    if "children" in garden:
        for child in garden["children"]:
            child = _remove_garden_history(child)

    return garden


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
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Garden'
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
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
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
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
        requestBody:
          name: patch
          description: Instructions for how to update the Garden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatchOperation'
        parameters:
          - name: garden_name
            in: path
            required: true
            description: Garden to use
            type: string
        responses:
          200:
            description: Garden with the given garden_name
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Garden'
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
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

            elif operation == "rescan":
                response = await self.process_operation(
                    Operation(
                        operation_type="GARDEN_RESCAN",
                        target_garden_name=garden.name,
                    )
                )

            elif operation == "sync":
                response = await self.process_operation(
                    Operation(
                        operation_type="GARDEN_SYNC",
                        target_garden_name=garden.name,
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
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Garden'
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
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
        requestBody:
          name: garden
          description: The Garden definition to create
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Garden'
        responses:
          201:
            description: A new Garden has been created
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Garden'
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
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

          * rescan
          * sync
          * sync_users

          ```JSON
          [
            { "operation": "" }
          ]
          ```
        requestBody:
          name: patch
          description: Instructions for how to update the Garden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PatchOperation'
        responses:
          204:
            description: Patch operation has been successfully forwarded
          400:
            description: Parameter validation error
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Parameter validation error
          404:
            description: Resource does not exist
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Resource does not exist
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
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
