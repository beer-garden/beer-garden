# -*- coding: utf-8 -*-
from brewtils.models import Operation

from beer_garden.api.authorization import Permissions
from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden

QUEUE_READ = Permissions.QUEUE_READ.value
QUEUE_DELETE = Permissions.QUEUE_DELETE.value


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
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Queues
        """
        self.verify_user_permission_for_object(QUEUE_DELETE, local_garden())

        await self.client(Operation(operation_type="QUEUE_DELETE", args=[queue_name]))

        self.set_status(204)


class QueueListAPI(AuthorizationHandler):
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
        self.verify_user_permission_for_object(QUEUE_READ, local_garden())

        response = await self.client(Operation(operation_type="QUEUE_READ"))

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

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
        self.verify_user_permission_for_object(QUEUE_DELETE, local_garden())

        await self.client(Operation(operation_type="QUEUE_DELETE_ALL"))

        self.set_status(204)
