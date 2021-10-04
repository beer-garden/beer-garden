from marshmallow import Schema, fields


class LoginInputSchema(Schema):
    """Schema for the user login input"""

    username = fields.Str(required=True, allow_none=False)
    password = fields.Str(required=True, allow_none=False)


class LoginResponseSchema(Schema):
    """Schema for the user login response"""

    token = fields.Str()
    message = fields.Str()
