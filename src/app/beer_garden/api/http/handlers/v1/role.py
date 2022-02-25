# -*- coding: utf-8 -*-

from beer_garden.api.http.handlers import AuthorizationHandler
from beer_garden.api.http.schemas.v1.role import RoleListSchema
from beer_garden.db.mongo.models import Role


class RoleListAPI(AuthorizationHandler):
    def get(self):
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
        roles = Role.objects.all()
        response = RoleListSchema().dump({"roles": roles}).data

        self.write(response)
