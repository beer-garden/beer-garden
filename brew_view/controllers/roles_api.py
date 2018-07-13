import logging

from mongoengine.errors import DoesNotExist

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
                try:
                    if op.operation == 'add':
                        role.permissions.append(Permissions(op.value).value)
                    elif op.operation == 'remove':
                        role.permissions.remove(Permissions(op.value).value)
                    elif op.operation == 'set':
                        role.permissions = [Permissions(perm).value for perm in op.value]
                    else:
                        raise ModelValidationError("Unsupported operation '%s'" % op.operation)
                except ValueError:
                    raise ModelValidationError("Permission '%s' does not exist"
                                               % op.value)

            elif op.path == '/roles':
                try:
                    if op.operation == 'add':
                        role.roles.append(Role.objects.get(name=op.value).to_dbref())
                    elif op.operation == 'remove':
                        role.roles.remove(Role.objects.get(name=op.value).to_dbref())
                    elif op.operation == 'set':
                        role.roles = [Role.objects.get(name=name).to_dbref() for name in op.value]
                    else:
                        raise ModelValidationError("Unsupported operation '%s'" % op.operation)
                except DoesNotExist:
                    raise ModelValidationError("Role '%s' does not exist" % op.value)

            else:
                raise ModelValidationError("Unsupported path '%s'" % op.path)

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

        # Make sure all new permissions are real
        if not set(role.permissions).issubset(Permissions.values):
            invalid = set(role.permissions).difference(Permissions.values)
            raise ModelValidationError("Permissions %s do not exist" % invalid)

        # And the same for nested roles
        nested_roles = []
        for nested_role in role.roles:
            try:
                nested_roles.append(Role.objects.get(name=nested_role.name).to_dbref())
            except DoesNotExist:
                raise ModelValidationError("Role '%s' does not exist" % nested_role.name)
        role.roles = nested_roles

        role.save()

        self.set_status(201)
        self.write(BeerGardenSchemaParser.serialize_role(role, to_string=False))
