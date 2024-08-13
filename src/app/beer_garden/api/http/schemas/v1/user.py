from marshmallow import Schema, fields, validate


class UserPasswordChangeSchema(Schema):
    """Schema for changing a user's password"""

    current_password = fields.Str(required=True)
    new_password = fields.Str(
        required=True, validate=validate.Length(min=1, error="Password required")
    )
