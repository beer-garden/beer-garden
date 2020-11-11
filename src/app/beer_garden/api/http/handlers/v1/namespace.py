# -*- coding: utf-8 -*-

from brewtils.models import Operation

from beer_garden.api.http.base_handler import BaseHandler


class NamespaceListAPI(BaseHandler):
    async def get(self):
        """
        ---
        summary: Get a list of all namespaces known to this garden
        responses:
          200:
            description: List of Namespaces
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """

        response = await self.client(Operation(operation_type="NAMESPACE_READ_ALL"))

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
