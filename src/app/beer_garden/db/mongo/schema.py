import brewtils.schemas
import brewtils.models

class MongoSchema:
    brewtils_model = None

    # Add schema if fields are excluded 
    mongo_schema = None

    collection = None

    indexes = []



class Request(MongoSchema):
    collection="request"
    brewtils_model = brewtils.models.Request
    mongo_schema  = brewtils.schemas.RequestSchema(exclude=("parent", "children"))
    indexes = [
            # These are used for sorting all requests
            {"name": "command_display_name_index", "fields": ["command_display_name"]},
            {"name": "command_type_index", "fields": ["command_type"]},
            {"name": "system_index", "fields": ["system"]},
            {"name": "instance_name_index", "fields": ["instance_name"]},
            {"name": "namespace_index", "fields": ["namespace"]},
            {"name": "status_index", "fields": ["status"]},
            {"name": "created_at_index", "fields": ["created_at"]},
            {"name": "status_updated_at_index", "fields": ["status_updated_at"]},
            {"name": "comment_index", "fields": ["comment"]},
            {"name": "parent_id_index", "fields": ["parent_id"]},
            {"name": "parent_index", "fields": ["has_parent"]},
            {"name": "hidden_index", "fields": ["hidden"]},
            # These are for sorting parent requests
            {
                "name": "parent_command_display_name_index",
                "fields": ["has_parent", "command_display_name"],
            },
            {"name": "parent_system_index", "fields": ["has_parent", "system"]},
            {
                "name": "parent_instance_name_index",
                "fields": ["has_parent", "instance_name"],
            },
            {"name": "parent_status_index", "fields": ["has_parent", "status"]},
            {"name": "parent_created_at_index", "fields": ["has_parent", "created_at"]},
            {"name": "parent_comment_index", "fields": ["has_parent", "comment"]},
            # These are used for filtering all requests while sorting on created time
            {
                "name": "created_at_command_display_name_index",
                "fields": ["-created_at", "command_display_name"],
            },
            {"name": "created_at_system_index", "fields": ["-created_at", "system"]},
            {
                "name": "created_at_instance_name_index",
                "fields": ["-created_at", "instance_name"],
            },
            {"name": "created_at_status_index", "fields": ["-created_at", "status"]},
            # These are used for filtering parent while sorting on created time
            {
                "name": "parent_created_at_command_display_name_index",
                "fields": ["has_parent", "-created_at", "command_display_name"],
            },
            {
                "name": "parent_created_at_system_index",
                "fields": ["has_parent", "-created_at", "system"],
            },
            {
                "name": "parent_created_at_instance_name_index",
                "fields": ["has_parent", "-created_at", "instance_name"],
            },
            {
                "name": "parent_created_at_status_index",
                "fields": ["has_parent", "-created_at", "status"],
            },
            # These are used for filtering hidden while sorting on created time
            # I THINK this makes the set of indexes above superfluous, but I'm keeping
            # both as a safety measure
            {
                "name": "hidden_parent_created_at_command_display_name_index",
                "fields": [
                    "hidden",
                    "has_parent",
                    "-created_at",
                    "command_display_name",
                ],
            },
            {
                "name": "hidden_parent_created_at_system_index",
                "fields": ["hidden", "has_parent", "-created_at", "system"],
            },
            {
                "name": "hidden_parent_created_at_instance_name_index",
                "fields": ["hidden", "has_parent", "-created_at", "instance_name"],
            },
            {
                "name": "hidden_parent_created_at_status_index",
                "fields": ["hidden", "has_parent", "-created_at", "status"],
            },
            # This is used for text searching
            {
                "name": "text_index",
                "fields": [
                    "$system",
                    "$command_display_name",
                    "$command_type",
                    "$comment",
                    "$status",
                    "$instance_name",
                ],
            },
        ]



class Topic(MongoSchema):
    collection="topic"
    brewtils_model = brewtils.models.Topic
    indexes= [{"name": "unique_index", "fields": ["name"], "unique": True}]
    


class System(MongoSchema):
    collection="topic"
    brewtils_model = brewtils.models.System
    indexes= [
            {
                "name": "unique_index",
                "fields": ["namespace", "name", "version"],
                "unique": True,
            }
        ]

    

class Event(MongoSchema):
    collection="event"
    brewtils_model = brewtils.models.Event



class Replication(MongoSchema):
    collection="replication"
    brewtils_model = brewtils.models.Replication
    indexes =  [
                {
                    "name": "expires_at_index",
                    "fields": ["expires_at"],
                    "expireAfterSeconds": 0,
                },
            ]
    

class Job(MongoSchema):
    collection="job"
    brewtils_model = brewtils.models.Job
    indexes = [
            {
                "name": "next_run_time_index",
                "fields": ["next_run_time"],
                "sparse": True,
            },
            {
                "name": "job_system_fields",
                "fields": [
                    "request_template.namespace",
                    "request_template.system",
                    "request_template.system_version",
                ],
            },
        ]



class Garden(MongoSchema):
    collection="garden"
    brewtils_model = brewtils.models.Garden
    mongo_schema = brewtils.schemas.GardenSchema(exclude=["children"])

    indexes = [
            {"name": "unique_index", "fields": ["name"], "unique": True},
            {
                "name": "local_unique_index",
                "fields": ["connection_type"],
                "unique": True,
                "partialFilterExpression": {"connection_type": "LOCAL"},
            },
        ]

    


class File(MongoSchema):
    collection="file"
    brewtils_model = brewtils.models.File
    mongo_schema = brewtils.schemas.FileSchema(exclude=["owner", "request", "job"])


class FileChunk(MongoSchema):
    collection="file_chunk"
    brewtils_model = brewtils.models.FileChunk
    mongo_schema = brewtils.schemas.FileChunkSchema(exclude=["owner"])


class RawFile(Document):
    collection="raw_file"
    brewtils_model = brewtils.models.Ra
    file = FileField()
    created_at = DateTimeField(default=get_current_time, required=True)
    request_id = StringField()

    # TTL Fields
    status = StringField()
    updated_at = DateTimeField(default=get_current_time, required=True)
    root_command_type = StringField()

    meta = {"queryset_class": FileFieldHandlingQuerySet}


class Role(MongoSchema):
    collection="role"
    brewtils_model = brewtils.models.Role
    indexes = [{"name": "unique_index", "fields": ["name"], "unique": True}]
   






class User(MongoSchema):
    collection="user"
    brewtils_model = brewtils.models.User
    mongo_schema = brewtils.schemas.UserSchema(exclude=["local_roles"])

    indexes = [{"name": "unique_index", "fields": ["username"], "unique": True}]


class UserToken(MongoSchema):
    collection="user_token"
    brewtils_model = brewtils.models.UserToken

    indexes =[
            {"name": "username_index", "fields": ["username"]},
            {"name": "uuid_index", "fields": ["uuid"]},
            {
                "name": "expires_at_index",
                "fields": ["expires_at"],
                "expireAfterSeconds": 0,
            },
        ]


class Configuration(MongoSchema):
    collection="configuration"
    # This is a snapshot of the configuration file last loaded
    # and is reset after migrations are completed. It should not
    # be used for optional configuration.
    action_ttl = IntField(default=-1)
    info_ttl = IntField(default=15)
    file_ttl = IntField(default=15)
    version = StringField(default="0.0.0")