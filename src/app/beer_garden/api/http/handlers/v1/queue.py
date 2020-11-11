# -*- coding: utf-8 -*-
from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler
from brewtils.models import Operation


class QueueAPI(BaseHandler):
    @authenticated(permissions=[Permissions.SYSTEM_ADMIN])
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

        await self.client(Operation(operation_type="QUEUE_DELETE", args=[queue_name]))

        self.set_status(204)


class QueueListAPI(BaseHandler):
    @authenticated(permissions=[Permissions.SYSTEM_ADMIN])
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

        response = await self.client(Operation(operation_type="QUEUE_READ"))

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)

    @authenticated(permissions=[Permissions.SYSTEM_ADMIN])
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

        await self.client(Operation(operation_type="QUEUE_DELETE_ALL"))

        self.set_status(204)
