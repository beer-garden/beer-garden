# -*- coding: utf-8 -*-
from brewtils.models import Garden, Operation, Permissions, Queue, System

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden


class QueueAPI(AuthorizationHandler):

    async def delete(self, queue_name):
        """
        ---
        summary: Clear a queue by canceling all requests
        parameters:
          - name: queue_name
            in: path
            required: true
            description: The name of the queue to clear
            type: string
        responses:
          204:
            description: Queue successfully cleared
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
          - Queues
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        self.get_or_raise(Queue, name=queue_name)

        await self.process_operation(
            Operation(operation_type="QUEUE_DELETE", args=[queue_name])
        )

        self.set_status(204)


class QueueListAPI(AuthorizationHandler):

    async def get(self):
        """
        ---
        summary: Retrieve all queue information
        responses:
          200:
            description: List of all queue information objects
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Queue'
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Queues
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        permitted_objects_filter = self.permitted_objects_filter(System)

        response = await self.process_operation(
            Operation(
                operation_type="QUEUE_READ",
                kwargs={
                    "q_filter": permitted_objects_filter,
                },
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    async def delete(self):
        """
        ---
        summary: Cancel and clear all requests in all queues
        parameters:
          - name: garden_name
            in: query
            required: false
            description: Specify garden to target
            type: string
        responses:
          204:
            description: All queues successfully cleared
          50x:
            description: Server Exception
            content:
              text/plain:
                schema:
                  type: 'string'
                example: Server Exception
        tags:
          - Queues
        """
        garden_name = self.get_query_argument("garden_name", None)

        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        if garden_name:
            self.get_or_raise(Garden, name=garden_name)
        else:
            self.verify_user_permission_for_object(local_garden())

        await self.process_operation(
            Operation(
                operation_type="QUEUE_DELETE_ALL",
                target_garden_name=garden_name,
            )
        )

        self.set_status(204)
