from apispec_pydantic_plugin import ApiBaseModel
from marshmallow import Schema, fields


class TokenInputSchema(Schema):
    """Schema for the user login input"""

    username = fields.Str(required=True, allow_none=False)
    password = fields.Str(required=True, allow_none=False)


class TokenInput(ApiBaseModel):
    username: str
    password: str


class TokenRefreshInputSchema(Schema):
    """Schema for the user login input"""

    refresh = fields.Str(required=True, allow_none=False)


class TokenRefreshInput(ApiBaseModel):
    refresh: str


class TokenResponseSchema(Schema):
    """Schema for the user login response"""

    access = fields.Str()
    refresh = fields.Str()


class TokenResponse(ApiBaseModel):
    access: str
    refresh: str
