import json

from bg_utils.models import Role
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.base_handler import BaseHandler


class RolesAPI(BaseHandler):

    def get(self):
        """
        ---
        summary: Retrieve all Roles
        responses:
          200:
            description: All Roles
            schema:
              type: array
              items:
                $ref: '#/definitions/Role'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(BeerGardenSchemaParser.serialize_role(Role.objects.all(),
                                                         many=True, to_string=True))

    def post(self):
        """
        ---
        summary: Create a new Role
        parameters:
          - name: role
            in: body
            description: The Role definition
            schema:
              $ref: '#/definitions/Role'
        consumes:
          - application/json
        responses:
          201:
            description: A new Role has been created
            schema:
              $ref: '#/definitions/Role'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        role = BeerGardenSchemaParser.parse_role(self.request.decoded_body,
                                                 from_string=True)
        role.save()

        self.set_status(201)
        self.write(BeerGardenSchemaParser.serialize_role(role, to_string=False))
