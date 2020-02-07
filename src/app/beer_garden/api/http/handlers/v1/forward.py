import json

import beer_garden
from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.router import Route_Type
from brewtils.schema_parser import SchemaParser


class ForwardAPI(BaseHandler):

    # @Todo Create new Persmission
    @authenticated(permissions=[Permissions.SYSTEM_UPDATE])
    async def post(self):
        """
        ---
        summary: Forward a request from a parent or child BG instance
        description: |
            When a Beer Garden needs to forward a request, this API will support routing
            to all CRUD actions exposed by the entry points.
        parameters:
          - name: route_class
            in: header
            required: true
            description: The Routing Path for the request
            type: string
          - name: obj_id
            in: header
            required: false
            description: For Read/Update/Delete actions, ID is required
            type: string
          - name: src_garden_name
            in: header
            required: false
            description: The sender of request. If empty, local Garden is default
            type: string
          - name: route_type
            in: header
            required: true
            description: The CRUD action that is being requested
            type: string
          - name: garden_name
            in: header
            required: false
            description: The target Garden Name to forward request to
            type: string
          - name: extra_kwargs
            in: header
            required: false
            description: Additional KWARG values to forward
            type: string
          - name: brewtils_obj
            in: body
            required: false
            description: The Brewtils Object being forwarded
            schema:
              oneOf:
                - $ref: '#/definitions/Command'
                - $ref: '#/definitions/Instance'
                - $ref: '#/definitions/Request'
                - $ref: '#/definitions/System'
                - $ref: '#/definitions/LoggingConfig'
                - $ref: '#/definitions/Event'
                - $ref: '#/definitions/Queue'
                - $ref: '#/definitions/Garden'
                - $ref: '#/definitions/Job'
                - $ref: '#/definitions/_patch'
        responses:
          200:
            description: Forward Request Accepted
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Forward
        """

        brewtils_obj = SchemaParser.parse(self.request.decoded_body, from_string=False)

        route_class = self.request.headers.get("route_class", None)
        obj_id = self.request.headers.get("obj_id", None)
        garden_name = self.request.headers.get("garden_name", None)
        src_garden_name = self.request.headers.get("src_garden_name", None)
        route_type = self.request.headers.get("route_type", None)
        extra_kwargs = self.request.headers.get("extra_kwargs", None)

        if extra_kwargs:
            extra_kwargs = json.load(extra_kwargs)

        response = await beer_garden.router.route_request(
            brewtils_obj=brewtils_obj,
            route_class=route_class,
            obj_id=obj_id,
            garden_name=garden_name,
            src_garden_name=src_garden_name,
            route_type=route_type,
            **extra_kwargs
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
