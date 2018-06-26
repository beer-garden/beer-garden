import logging

from bg_utils.models import Role
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.authorization import Permissions
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError


class RoleAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    def get(self, role_id):
        """
        ---
        summary: Retrieve all specific Role
        parameters:
          - name: role_id
            in: path
            required: true
            description: The ID of the Role
            type: string
        responses:
          200:
            description: Role with the given ID
            schema:
              $ref: '#/definitions/Role'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        self.write(BeerGardenSchemaParser.serialize_role(
            Role.objects.get(id=str(role_id)),
            to_string=False
        ))

    def delete(self, role_id):
        """
        ---
        summary: Delete a specific Role
        parameters:
          - name: role_id
            in: path
            required: true
            description: The ID of the Role
            type: string
        responses:
          204:
            description: Role has been successfully deleted
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        role = Role.objects.get(id=str(role_id))
        role.delete()

        self.set_status(204)

    def patch(self, role_id):
        """
        ---
        summary: Partially update a Role
        description: |
          The body of the request needs to contain a set of instructions
          detailing the updates to apply:
          ```JSON
          {
            "operations": [
              { "operation": "add", "path": "/permissions", "value": "ALL" }
            ]
          }
          ```
        parameters:
          - name: role_id
            in: path
            required: true
            description: The ID of the Role
            type: string
          - name: patch
            in: body
            required: true
            description: Instructions for how to update the Role
            schema:
              $ref: '#/definitions/Patch'
        responses:
          200:
            description: Role with the given ID
            schema:
              $ref: '#/definitions/Role'
          400:
            $ref: '#/definitions/400Error'
          404:
            $ref: '#/definitions/404Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Roles
        """
        role = Role.objects.get(id=str(role_id))
        operations = BeerGardenSchemaParser.parse_patch(
            self.request.decoded_body,
            many=True,
            from_string=True
        )

        for op in operations:
            if op.path == '/permissions':
                if op.value.upper() not in Permissions.__members__:
                    error_msg = "Permission '%s' does not exist" % op.value
                    self.logger.warning(error_msg)
                    raise ModelValidationError(error_msg)

                if op.operation == 'add':
                    role.permissions.append(op.value.upper())
                elif op.operation == 'remove':
                    role.permissions.remove(op.value.upper())
                else:
                    error_msg = "Unsupported operation '%s'" % op.operation
                    self.logger.warning(error_msg)
                    raise ModelValidationError(error_msg)

            else:
                error_msg = "Unsupported path '%s'" % op.path
                self.logger.warning(error_msg)
                raise ModelValidationError(error_msg)

        role.save()

        self.write(BeerGardenSchemaParser.serialize_role(role, to_string=False))


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
