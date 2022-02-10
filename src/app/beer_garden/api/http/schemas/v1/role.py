from brewtils.schemas import RoleSchema
from marshmallow import Schema, fields


class RoleListSchema(Schema):
    """Schema for listing multiple roles"""

    roles = fields.List(fields.Nested(RoleSchema))
