# -*- coding: utf-8 -*-
import logging

from brewtils.errors import ModelValidationError
from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser

from beer_garden.api.authorization import Permissions
from beer_garden.api.http.handlers import AuthorizationHandler

# from beer_garden.authorization import user_has_permission_for_object
from beer_garden.db.mongo.models import Garden
from beer_garden.garden import local_garden
from beer_garden.user import initiate_user_sync

GARDEN_CREATE = Permissions.GARDEN_CREATE.value
GARDEN_READ = Permissions.GARDEN_READ.value
GARDEN_UPDATE = Permissions.GARDEN_UPDATE.value
GARDEN_DELETE = Permissions.GARDEN_DELETE.value


logger = logging.getLogger(__name__)


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

        response = await self.client(
            Operation(operation_type="GARDEN_READ", args=[garden_name])
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

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
        garden = self.get_or_raise(Garden, GARDEN_DELETE, name=garden_name)

        await self.client(Operation(operation_type="GARDEN_DELETE", args=[garden.name]))

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
        garden = self.get_or_raise(Garden, GARDEN_UPDATE, name=garden_name)

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation in ["initializing", "running", "stopped", "block"]:
                response = await self.client(
                    Operation(
                        operation_type="GARDEN_UPDATE_STATUS",
                        args=[garden.name, operation.upper()],
                    )
                )
            elif operation == "heartbeat":
                response = await self.client(
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
                    response = await self.client(
                        Operation(
                            operation_type="GARDEN_UPDATE_PUBLISHING_STATUS",
                            kwargs={"garden_name": garden.name, "api": api},
                            args=[status],
                        )
                    )
                elif connection_type.upper() == "RECEIVING":
                    response = await self.client(
                        Operation(
                            operation_type="GARDEN_UPDATE_RECEIVING_STATUS",
                            kwargs={"garden_name": garden.name, "api": api},
                            args=[status],
                        )
                    )

            elif operation == "sync":
                response = await self.client(
                    Operation(
                        operation_type="GARDEN_SYNC",
                        kwargs={"sync_target": garden.name},
                    )
                )

            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)


class GardenListAPI(AuthorizationHandler):
    async def get(self):
        """
        ---
        summary: Retrieve a list of Gardens
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
        # permitted_gardens = self.permissioned_queryset(Garden, GARDEN_READ)
        # response_gardens = []

        # permitted_gardens_list = list(
        #     permitted_gardens.filter(connection_type__ne="LOCAL").no_cache()
        # )
        # _local_garden = local_garden(all_systems=True)

        # if user_has_permission_for_object(
        #     self.current_user, GARDEN_READ, _local_garden
        # ):
        #     permitted_gardens_list.append(_local_garden)

        permitted_gardens_list = await self.client(
            Operation(operation_type="GARDEN_READ_ALL")
        )
        self.write(permitted_gardens_list)

        # response_gardens = []
        # for garden in SchemaParser.parse_garden(
        #     permitted_gardens_list, from_string=True, many=True
        # ):
        #     if user_has_permission_for_object(self.current_user, GARDEN_READ, garden):
        #         response_gardens.append(garden)

        # self.set_header("Content-Type", "application/json; charset=UTF-8")

        # self.write(
        #     SchemaParser.serialize_garden(response_gardens, to_string=True, many=True)
        # )

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
        garden = SchemaParser.parse_garden(self.request.decoded_body, from_string=True)

        self.verify_user_permission_for_object(GARDEN_CREATE, garden)

        response = await self.client(
            Operation(
                operation_type="GARDEN_CREATE",
                args=[garden],
            )
        )

        self.set_status(201)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

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
        self.verify_user_permission_for_object(GARDEN_UPDATE, local_garden())

        patch = SchemaParser.parse_patch(self.request.decoded_body, from_string=True)

        for op in patch:
            operation = op.operation.lower()

            if operation == "rescan":
                await self.client(
                    Operation(
                        operation_type="GARDEN_RESCAN",
                    )
                )

            elif operation == "sync":
                await self.client(
                    Operation(
                        operation_type="GARDEN_SYNC",
                    )
                )
            elif operation == "sync_users":
                # requires GARDEN_UPDATE for all gardens
                for garden in Garden.objects.all():
                    self.verify_user_permission_for_object(GARDEN_UPDATE, garden)

                initiate_user_sync()
            else:
                raise ModelValidationError(f"Unsupported operation '{op.operation}'")

        self.set_status(204)
