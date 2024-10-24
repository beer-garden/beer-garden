# -*- coding: utf-8 -*-
import asyncio

from brewtils.errors import TimeoutExceededError
from brewtils.models import Permissions
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.metrics import collect_metrics


class ForwardAPI(AuthorizationHandler):

    @collect_metrics(transaction_type="API", group="ForwardAPI")
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
          204:
            description: Forward Request Accepted
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Forward
        """
        self.minimum_permission = Permissions.GARDEN_ADMIN.name
        self.verify_user_global_permission()

        operation = SchemaParser.parse_operation(
            self.request.decoded_body, from_string=True
        )

        task = asyncio.create_task(
            self.process_operation(operation, filter_results=False)
        )

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
