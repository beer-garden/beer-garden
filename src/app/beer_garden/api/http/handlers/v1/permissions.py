# -*- coding: utf-8 -*-
import json
import logging

from beer_garden.api.http.authorization import authenticated, Permissions
from beer_garden.api.http.base_handler import BaseHandler


class PermissionsAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.LOCAL_ADMIN])
    def get(self):
        """
        ---
        summary: Retrieve all Permissions
        responses:
          200:
            description: All Permissions
            schema:
              type: array
              items:
                type: string
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Permissions
        """
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(sorted(Permissions.values)))
