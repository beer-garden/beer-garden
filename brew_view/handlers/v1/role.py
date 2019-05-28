import logging

from mongoengine.errors import DoesNotExist

import brew_view
from bg_utils.mongo.models import Role
from bg_utils.mongo.parser import MongoParser
from brew_view.authorization import anonymous_principal, authenticated, Permissions
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError


class RoleAPI(BaseHandler):

    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.ROLE_READ])
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
        self.write(
            MongoParser.serialize_role(
                Role.objects.get(id=str(role_id)), to_string=False
            )
        )

    @authenticated(permissions=[Permissions.ROLE_DELETE])
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
        if role.name in ("bg-admin", "bg-anonymous", "bg-plugin"):
            raise ModelValidationError("Unable to remove '%s' role" % role.name)

        role.delete()

        self.set_status(204)

    @authenticated(permissions=[Permissions.ROLE_UPDATE])
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
        operations = MongoParser.parse_patch(
            self.request.decoded_body, many=True, from_string=True
        )

        for op in operations:
            if op.path == "/permissions":
                try:
                    if op.operation == "add":
                        role.permissions.append(Permissions(op.value).value)
                    elif op.operation == "remove":
                        role.permissions.remove(Permissions(op.value).value)
                    elif op.operation == "set":
                        role.permissions = [
                            Permissions(perm).value for perm in op.value
                        ]
                    else:
                        raise ModelValidationError(
                            "Unsupported operation '%s'" % op.operation
                        )
                except ValueError:
                    raise ModelValidationError(
                        "Permission '%s' does not exist" % op.value
                    )

            elif op.path == "/roles":
                try:
                    if op.operation == "add":
                        new_nested = Role.objects.get(name=op.value)
                        ensure_no_cycles(role, new_nested)
                        role.roles.append(new_nested)
                    elif op.operation == "remove":
                        role.roles.remove(Role.objects.get(name=op.value))
                    elif op.operation == "set":
                        # Do this one at a time to be super sure about cycles
                        role.roles = []

                        for role_name in op.value:
                            new_role = Role.objects.get(name=role_name)
                            ensure_no_cycles(role, new_role)
                            role.roles.append(new_role)
                    else:
                        raise ModelValidationError(
                            "Unsupported operation '%s'" % op.operation
                        )
                except DoesNotExist:
                    raise ModelValidationError("Role '%s' does not exist" % op.value)

            elif op.path == "/description":
                if op.operation != "update":
                    raise ModelValidationError(
                        "Unsupported operation '%s'" % op.operation
                    )
                role.description = op.value

            else:
                raise ModelValidationError("Unsupported path '%s'" % op.path)

        role.save()

        # Any modification to roles will possibly modify the anonymous user
        brew_view.anonymous_principal = anonymous_principal()

        self.write(MongoParser.serialize_role(role, to_string=False))


class RolesAPI(BaseHandler):
    @authenticated(permissions=[Permissions.ROLE_READ])
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
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(
            MongoParser.serialize_role(Role.objects.all(), many=True, to_string=True)
        )

    @authenticated(permissions=[Permissions.ROLE_CREATE])
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
        role = MongoParser.parse_role(self.request.decoded_body, from_string=True)

        # Make sure all new permissions are real
        if not set(role.permissions).issubset(Permissions.values):
            invalid = set(role.permissions).difference(Permissions.values)
            raise ModelValidationError("Permissions %s do not exist" % invalid)

        # And the same for nested roles
        nested_roles = []
        for nested_role in role.roles:
            try:
                db_role = Role.objects.get(name=nested_role.name)

                # There shouldn't be any way to construct a cycle with a new
                # role, but check just to be sure
                ensure_no_cycles(role, db_role)

                nested_roles.append(db_role)
            except DoesNotExist:
                raise ModelValidationError(
                    "Role '%s' does not exist" % nested_role.name
                )
        role.roles = nested_roles

        role.save()

        self.set_status(201)
        self.write(MongoParser.serialize_role(role, to_string=False))


def ensure_no_cycles(base_role, new_role):
    """Make sure there are no nested role cycles

    Do this by looking through new_roles's nested roles and making sure
    base_role doesn't appear

    Args:
        base_role: The role that is being modified
        new_role: The new nested role

    Returns:
        None

    Raises:
        ModelValidationError: A cycle was detected
    """
    for role in new_role.roles:
        if role == base_role:
            raise ModelValidationError("Cycle Detected!")

        ensure_no_cycles(base_role, role)
