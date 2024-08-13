# -*- coding: utf-8 -*-
from brewtils.models import Operation, Permissions, Queue, System

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden
from beer_garden.metrics import collect_metrics


class QueueAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="QueueAPI")
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
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
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

    @collect_metrics(transaction_type="API", group="QueueListAPI")
    async def get(self):
        """
        ---
        summary: Retrieve all queue information
        responses:
          200:
            description: List of all queue information objects
            schema:
              type: array
              items:
                $ref: '#/definitions/Queue'
          50x:
            $ref: '#/definitions/50xError'
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

    @collect_metrics(transaction_type="API", group="QueueListAPI")
    async def delete(self):
        """
        ---
        summary: Cancel and clear all requests in all queues
        responses:
          204:
            description: All queues successfully cleared
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Queues
        """
        self.minimum_permission = Permissions.PLUGIN_ADMIN.name
        self.verify_user_permission_for_object(local_garden())

        await self.process_operation(Operation(operation_type="QUEUE_DELETE_ALL"))

        self.set_status(204)
