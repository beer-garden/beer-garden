from brewtils.schemas import PatchSchema
from marshmallow import Schema, fields


class PatchOperationSchema(Schema):
    """Schema for Patch Operaitons"""

    operations = fields.List(fields.Nested(lambda: PatchSchema), allow_none=True)
