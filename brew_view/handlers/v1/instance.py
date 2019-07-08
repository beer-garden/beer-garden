from tornado.gen import coroutine

from brew_view import thrift_context
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler


class InstanceAPI(BaseHandler):
    @coroutine
    @authenticated(permissions=[Permissions.INSTANCE_READ])
    def get(self, instance_id):
        """
        ---
        summary: Retrieve a specific Instance
        parameters:
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
        with thrift_context() as client:
            thrift_response = yield client.getInstance(instance_id)

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)

    @coroutine
    @authenticated(permissions=[Permissions.INSTANCE_DELETE])
    def delete(self, instance_id):
        """
        ---
        summary: Delete a specific Instance
        parameters:
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
        with thrift_context() as client:
            yield client.removeInstance(instance_id)

        self.set_status(204)

    @coroutine
    @authenticated(permissions=[Permissions.INSTANCE_UPDATE])
    def patch(self, instance_id):
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
          {
            "operations": [
              { "operation": "" }
            ]
          }
          ```
        parameters:
          - name: instance_id
            in: path
            required: true
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
        with thrift_context() as client:
            thrift_response = yield client.updateInstance(
                instance_id, self.request.decoded_body
            )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(thrift_response)
