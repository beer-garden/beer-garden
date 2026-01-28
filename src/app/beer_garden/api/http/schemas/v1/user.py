from marshmallow import Schema, fields, validate


class UserPasswordChangeSchema(Schema):
    """Schema for changing a user's password"""

    current_password = fields.Str(required=True)
    new_password = fields.Str(
        required=True, validate=validate.Length(min=1, error="Password required")
    )


from apispec_pydantic_plugin import ApiBaseModel
from pydantic import BaseModel, Field, field_validator


class UserPasswordChange(ApiBaseModel):
    """Schema for changing a user's password"""

    current_password: str
    new_password: str  # = Field(min_length=1)

    @field_validator("new_password")
    def new_password_min_length(cls, v):
        if len(v) < 1:
            raise ValueError("Password required")

        return v
