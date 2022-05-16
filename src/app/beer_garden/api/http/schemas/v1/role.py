from brewtils.schemas import RoleSchema as BrewtilsRoleSchema
from marshmallow import Schema, fields, pre_dump


class RoleSchema(BrewtilsRoleSchema):
    sync_status = fields.Dict(dump_only=True)

    @pre_dump(pass_many=True)
    def get_sync_status(self, data, many):
        """Add the status of whether each role is synced with each remote garden"""
        from beer_garden.role import role_sync_status

        roles = data if many else [data]
        sync_status = role_sync_status(roles)

        for role in roles:
            role.sync_status = sync_status.get(role.name)


class RoleListSchema(Schema):
    """Schema for listing multiple roles"""

    roles = fields.List(fields.Nested(RoleSchema))
