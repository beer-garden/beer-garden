# -*- coding: utf-8 -*-
import asyncio

from brewtils.errors import TimeoutExceededError
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import BaseHandler


class ForwardAPI(BaseHandler):

    # @Todo Create new Persmission
    async def post(self):
        """
        ---
        summary: Forward a request from a parent or child BG instance
        description: |
            When a Beer Garden needs to forward a request, this API will support routing
            to all CRUD actions exposed by the entry points.
        parameters:
          - name: blocking
            in: query
            required: false
            description: Flag indicating whether to wait for request completion
            type: boolean
            default: false
          - name: timeout
            in: query
            required: false
            description: Max seconds to wait for request completion. (-1 = wait forever)
            type: float
            default: -1
          - name: forward
            in: body
            required: true
            description: The Forward Object
            schema:
                $ref: '#/definitions/Forward'
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
        operation = SchemaParser.parse_operation(
            self.request.decoded_body, from_string=True
        )

        task = asyncio.create_task(self.client(operation))

        # Deal with blocking
        blocking = self.get_argument("blocking", default="").lower() == "true"
        if not blocking:
            self.set_status(204)
        else:
            timeout = float(self.get_argument("timeout", default="-1"))

            done, _ = await asyncio.wait({task}, timeout=timeout)

            if not done:
                raise TimeoutExceededError("Timeout exceeded")

            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.write(done.result())
