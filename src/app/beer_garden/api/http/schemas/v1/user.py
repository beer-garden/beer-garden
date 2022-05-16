from brewtils.schemas import RoleAssignmentDomainSchema, RoleAssignmentSchema
from brewtils.schemas import UserSchema as BrewtilsUserSchema
from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_dump,
    post_load,
    pre_dump,
    validate,
)

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
    hashed_password = fields.Str()
    role_assignments = fields.List(fields.Nested(RoleAssignmentPatchSchema))


class UserPasswordChangeSchema(Schema):
    """Schema for changing a user's password"""

    current_password = fields.Str(required=True)
    new_password = fields.Str(
        required=True, validate=validate.Length(min=1, error="Password required")
    )


class UserSyncSchema(Schema):
    """Schema for syncing Users between gardens"""

    username = fields.Str()
    password = fields.Str(dump_to="hashed_password")
    role_assignments = fields.List(fields.Nested(RoleAssignmentSchema()))

    @post_dump(pass_many=True)
    def dump_obj(self, data, many=False, **kwargs):
        """Drop the role definition in favor of just the role_name so that we can use
        UserPatchSchema on the other end of the sync"""
        if many is False:
            data = [data]

        for item in data:
            for assignment in item.get("role_assignments", []):
                assignment["role_name"] = assignment.pop("role")["name"]


class UserSchema(BrewtilsUserSchema):
    sync_status = fields.Dict(dump_only=True)

    @pre_dump(pass_many=True)
    def get_sync_status(self, data, many):
        """Add the status of whether each user is synced with each remote garden"""
        from beer_garden.user import user_sync_status

        users = data if many else [data]
        sync_status = user_sync_status(users)

        for user in users:
            user.sync_status = sync_status.get(user.username)


class UserListSchema(Schema):
    users = fields.List(fields.Nested(UserSchema()))
