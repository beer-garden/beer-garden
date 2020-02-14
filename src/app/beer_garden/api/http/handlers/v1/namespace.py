import json

import beer_garden
from beer_garden.api.http.authorization import Permissions, authenticated
from beer_garden.api.http.base_handler import BaseHandler

class NamespaceAPI(BaseHandler):

    @authenticated(permissions=[Permissions.SYSTEM_READ])
    async def get(self):
        """
        ---
        summary: Get the default namespace
        responses:
          200:
            description: Default Namespace
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Namespace
        """

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(beer_garden.config.get("namespaces.local"))
