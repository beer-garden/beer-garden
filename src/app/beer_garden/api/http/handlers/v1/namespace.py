# -*- coding: utf-8 -*-

from brewtils.models import Operation

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.db.mongo.models import Garden, Request, System


class NamespaceListAPI(AuthorizationHandler):
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
        self.minimum_permission = self.READ_ONLY
        permitted_gardens = self.permissioned_queryset(Garden)
        permitted_requests = self.permissioned_queryset(Request)
        permitted_systems = self.permissioned_queryset(System)

        response = await self.process_operation(
            Operation(
                operation_type="NAMESPACE_READ_ALL",
                kwargs={
                    "garden_queryset": permitted_gardens,
                    "system_queryset": permitted_systems,
                    "request_queryset": permitted_requests,
                },
            )
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
