from marshmallow import Schema, fields


class CommandPublishingBlocklistSchema(Schema):
    """Schema for the command publishing block list"""

    namespace = fields.Str(required=True)
    system = fields.Str(required=True)
    command = fields.Str(required=True)
