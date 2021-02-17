# -*- coding: utf-8 -*-
import logging

from beer_garden.api.http.base_handler import BaseHandler
from beer_garden.errors import EndpointRemovedException


class PermissionsAPI(BaseHandler):

    logger = logging.getLogger(__name__)

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
        raise EndpointRemovedException
