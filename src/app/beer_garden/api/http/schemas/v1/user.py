from brewtils.schemas import RoleAssignmentDomainSchema
from marshmallow import Schema, ValidationError, fields, post_load, validate

from beer_garden.db.mongo.models import Role, RoleAssignment, RoleAssignmentDomain


class RoleAssignmentPatchSchema(Schema):
    """Schema for setting user role assignments. Converts the supplied role name or id
    to a proper Role Document object"""

    domain = fields.Nested(RoleAssignmentDomainSchema)
    role_id = fields.Str()
    role_name = fields.Str()

    @post_load
    def load_obj(self, item, **kwargs):
        role_id = item.get("role_id")
        role_name = item.get("role_name")

        role_assignment = RoleAssignment(
            domain=RoleAssignmentDomain(
                scope=item["domain"].get("scope"),
                identifiers=item["domain"].get("identifiers"),
            )
        )

        try:
            if role_id:
                role_assignment.role = Role.objects.get(id=role_id)
            elif role_name:
                role_assignment.role = Role.objects.get(name=role_name)
            else:
                raise ValidationError("Either role_id or role_name must be specified")
        except Role.DoesNotExist:
            raise ValidationError(
                f"Could not find role with id = {role_id} or name = {role_name}"
            )

        return role_assignment


class UserPatchSchema(Schema):
    """Schema for updating Users"""

    password = fields.Str()
    role_assignments = fields.List(fields.Nested(RoleAssignmentPatchSchema))


class UserPasswordChangeSchema(Schema):
    """Schema for changing a user's password"""

    current_password = fields.Str(required=True)
    new_password = fields.Str(
        required=True, validate=validate.Length(min=1, error="Password required")
    )
