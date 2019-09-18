from beer_garden.api.brew_view.authorization import authenticated, Permissions
from beer_garden.api.brew_view.base_handler import BaseHandler
from beer_garden.api.brew_view.thrift import ThriftClient


class QueueAPI(BaseHandler):
    @authenticated(permissions=[Permissions.QUEUE_DELETE])
    async def delete(self, queue_name):
        """
        ---
        summary: Clear a queue by canceling all requests
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
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
        async with ThriftClient() as client:
            await client.clearQueue(self.request.namespace, queue_name)

        self.set_status(204)


class QueueListAPI(BaseHandler):
    @authenticated(permissions=[Permissions.QUEUE_READ])
    async def get(self):
        """
        ---
        summary: Retrieve all queue information
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
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
        async with ThriftClient() as client:
            queues = await client.getAllQueueInfo(self.request.namespace)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(queues)

    @authenticated(permissions=[Permissions.QUEUE_DELETE])
    async def delete(self):
        """
        ---
        summary: Cancel and clear all requests in all queues
        parameters:
          - name: bg-namespace
            in: header
            required: false
            description: Namespace to use
            type: string
        responses:
          204:
            description: All queues successfully cleared
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Queues
        """
        async with ThriftClient() as client:
            await client.clearAllQueues(self.request.namespace)

        self.set_status(204)
