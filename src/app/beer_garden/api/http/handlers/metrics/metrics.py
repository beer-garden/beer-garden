# -*- coding: utf-8 -*-

from brewtils.models import Operation
from brewtils.schema_parser import SchemaParser

from beer_garden.api.http.base_handler import BaseHandler


class MetricsAPI(BaseHandler):
    parser = SchemaParser()

    async def get(self):
        """
        ---
        summary: Retrieve metrics
        responses:
          200:
            description: List of metrics
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Metrics
        """

        response = await self.client(
            Operation(
                operation_type="METRICS_READ",
            ),
            serialize_kwargs={"return_raw": True},
        )

        self.set_header("Content-Type", "text/plain; charset=UTF-8")
        self.write(response)
