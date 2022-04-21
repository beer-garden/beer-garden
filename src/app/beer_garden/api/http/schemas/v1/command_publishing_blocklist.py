from marshmallow import Schema, fields


class CommandPublishingBlocklistInputSchema(Schema):
    """Schema for the command publishing block list input"""

    namespace = fields.Str(required=True)
    system = fields.Str(required=True)
    command = fields.Str(required=True)


class CommandPublishingBlocklistListInputSchema(Schema):
    command_publishing_blocklist = fields.List(
        fields.Nested(CommandPublishingBlocklistInputSchema())
    )


class CommandPublishingBlocklistSchema(Schema):
    """Schema for the command publishing block list"""

    namespace = fields.Str(required=True)
    system = fields.Str(required=True)
    command = fields.Str(required=True)
    status = fields.Str(required=False)
    id = fields.Str(required=False)


class CommandPublishingBlocklistListSchema(Schema):
    command_publishing_blocklist = fields.List(
        fields.Nested(CommandPublishingBlocklistSchema())
    )
