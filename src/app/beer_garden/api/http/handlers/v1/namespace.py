# -*- coding: utf-8 -*-
import json

from brewtils.errors import ModelValidationError
from beer_garden.api.http.base_handler import BaseHandler
from brewtils.models import Operation


class NamespaceAPI(BaseHandler):
    async def get(self):
        """
        ---
        summary: Get the List of Name Spaces on the Garden
        responses:
          200:
            description: List of Name Spaces on Garden
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """

        response = await self.client(Operation(operation_type="NAMESPACES_READ_ALL"))

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
