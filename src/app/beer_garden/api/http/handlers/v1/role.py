# -*- coding: utf-8 -*-

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.garden import local_garden

from brewtils.models import Operation


class RoleListAPI(AuthorizationHandler):
    async def get(self):
        """
        ---
        summary: Retrieve all Roles
        responses:
          200:
            description: All Roles
            schema:
              $ref: '#/definitions/RoleList'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        self.minimum_permission = self.GARDEN_ADMIN
        self.verify_user_permission_for_object(local_garden())

        response = await self.process_operation(
            Operation(operation_type="ROLE_READ_ALL")
        )

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(response)
