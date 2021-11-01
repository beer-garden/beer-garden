from marshmallow import Schema, fields


class TokenInputSchema(Schema):
    """Schema for the user login input"""

    username = fields.Str(required=True, allow_none=False)
    password = fields.Str(required=True, allow_none=False)


class TokenRefreshInputSchema(Schema):
    """Schema for the user login input"""

    refresh = fields.Str(required=True, allow_none=False)


class TokenResponseSchema(Schema):
    """Schema for the user login response"""

    access = fields.Str()
    refresh = fields.Str()
