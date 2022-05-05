from brewtils.schemas import RoleSchema as BrewtilsRoleSchema
from marshmallow import Schema, fields, pre_dump


class RoleSchema(BrewtilsRoleSchema):
    sync_status = fields.Dict(dump_only=True)

    @pre_dump
    def get_sync_status(self, role):
        from beer_garden.role import role_sync_status

        role.sync_status = role_sync_status(role)


class RoleListSchema(Schema):
    """Schema for listing multiple roles"""

    roles = fields.List(fields.Nested(RoleSchema))
