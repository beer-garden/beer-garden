# -*- coding: utf-8 -*-
import datetime
import logging
import zoneinfo

import brewtils.models
from brewtils.errors import ModelValidationError
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import Job as BrewtilsJob
from brewtils.models import Parameter as BrewtilsParameter
from brewtils.models import Request as BrewtilsRequest
from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    DynamicField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    GenericEmbeddedDocumentField,
    IntField,
    ListField,
    ObjectIdField,
    StringField,
)

from beer_garden.db.mongo.querysets import FileFieldHandlingQuerySet

from .fields import DummyField

__all__ = [
    "System",
    "StatusHistory",
    "StatusInfo",
    "Instance",
    "Command",
    "Connection",
    "Parameter",
    "Request",
    "Choices",
    "Event",
    "UserToken",
    "Job",
    "RequestTemplate",
    "DateTrigger",
    "CronTrigger",
    "IntervalTrigger",
    "FileTrigger",
    "Garden",
    "File",
    "FileChunk",
    "Role",
    "UpstreamRole",
    "AliasUserMap",
    "User",
    "Topic",
    "Subscriber",
    "Replication",
]

REQUEST_MAX_PARAM_SIZE = 5 * 1_000_000

logger = logging.getLogger(__name__)


def get_current_time():
    return datetime.datetime.now(tz=datetime.timezone.utc)


class MongoModel:
    brewtils_model = None

    def __str__(self):
        return self.brewtils_model.__str__(self)

    def __repr__(self):
        return self.brewtils_model.__repr__(self)

    @classmethod
    def index_names(cls):
        return [index["name"] for index in cls._meta["indexes"]]

    def save(self, *args, **kwargs):
        kwargs.setdefault("write_concern", {"w": "majority"})
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Sigh. In delete (but not save!) write_concern things ARE the kwargs!
        kwargs.setdefault("w", "majority")
        return super().delete(*args, **kwargs)

    def clean_update(self):
        pass

    def pre_serialize(self):
        pass

    @property
    def changed_fields(self):
        return getattr(self, "_changed_fields", [])

    @property
    def created(self):
        return getattr(self, "_created", False)


# MongoEngine needs all EmbeddedDocuments to be defined before any Documents that
# reference them. So Parameter must be defined before Command, and choices should be
# defined before Parameter


class Choices(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Choices

    display = StringField(required=True, choices=brewtils.models.Choices.DISPLAYS)
    strict = BooleanField(required=True, default=True)
    type = StringField(
        required=True, default="static", choices=brewtils.models.Choices.TYPES
    )
    value = DynamicField(required=True)
    details = DictField()


class Parameter(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Parameter

    key = StringField(required=True)
    type = StringField(required=True)
    multi = BooleanField(required=True, default=False)
    display_name = StringField(required=False)
    optional = BooleanField(required=True, default=True)
    default = DynamicField(required=False, default=None)
    description = StringField(required=False)
    choices = EmbeddedDocumentField("Choices", default=None)
    nullable = BooleanField(required=False, default=False)
    maximum = IntField(required=False)
    minimum = IntField(required=False)
    regex = StringField(required=False)
    form_input_type = StringField(
        required=False, choices=BrewtilsParameter.FORM_INPUT_TYPES
    )
    type_info = DictField(required=False)
    parameters = EmbeddedDocumentListField("Parameter")


class Command(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Command

    name = StringField(required=True)
    display_name = StringField()
    description = StringField()
    parameters = EmbeddedDocumentListField("Parameter")
    command_type = StringField()
    output_type = StringField()
    schema = DictField()
    form = DictField()
    template = StringField()
    hidden = BooleanField()
    icon_name = StringField()
    metadata = DictField()
    tags = ListField(field=StringField())
    topics = ListField(field=StringField())
    allow_any_kwargs = BooleanField(default=False)


class StatusHistory(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.StatusHistory

    heartbeat = DateTimeField()
    status = StringField()


class StatusInfo(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.StatusInfo

    heartbeat = DateTimeField()
    history = EmbeddedDocumentListField("StatusHistory")


def generate_objectid():
    return ObjectIdField().to_python(None)


class Instance(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Instance
    id = ObjectIdField(
        required=True, default=generate_objectid, unique=True, primary_key=True
    )
    name = StringField(required=True, default="default")
    description = StringField()
    status = StringField(default="INITIALIZING")
    status_info = EmbeddedDocumentField("StatusInfo")
    queue_type = StringField()
    queue_info = DictField()
    icon_name = StringField()
    metadata = DictField()


class Request(MongoModel, Document):
    brewtils_model = brewtils.models.Request

    # These fields are duplicated for job types, changes to this field
    # necessitate a change to the RequestTemplateSchema in brewtils.
    TEMPLATE_FIELDS = {
        "system": {"field": StringField, "kwargs": {"required": True}},
        "system_version": {"field": StringField, "kwargs": {"required": True}},
        "instance_name": {"field": StringField, "kwargs": {"required": True}},
        "namespace": {"field": StringField, "kwargs": {"required": False}},
        "command": {"field": StringField, "kwargs": {"required": True}},
        "command_display_name": {"field": StringField, "kwargs": {"required": False}},
        "command_type": {"field": StringField, "kwargs": {}},
        "parameters": {"field": DictField, "kwargs": {}},
        "comment": {"field": StringField, "kwargs": {"required": False}},
        "metadata": {"field": DictField, "kwargs": {}},
        "output_type": {"field": StringField, "kwargs": {}},
    }

    for field_name, field_info in TEMPLATE_FIELDS.items():
        locals()[field_name] = field_info["field"](**field_info["kwargs"])

    # Shared field with RequestTemplate, but it is required when saving Request
    namespace = StringField(required=True)

    parent = DummyField(required=False)
    parent_id = StringField()
    children = DummyField(required=False)
    output = StringField()
    output_type = StringField(choices=BrewtilsCommand.OUTPUT_TYPES)
    status = StringField(choices=BrewtilsRequest.STATUS_LIST, default="CREATED")
    command_type = StringField(choices=BrewtilsCommand.COMMAND_TYPES)
    created_at = DateTimeField(default=get_current_time, required=True)
    updated_at = DateTimeField(default=get_current_time, required=True)
    status_updated_at = DateTimeField()
    error_class = StringField(required=False)
    has_parent = BooleanField(required=False)
    hidden = BooleanField(required=False, default=False)
    requester = StringField(required=False)
    is_event = BooleanField(required=False)
    source_garden = StringField(required=False)
    target_garden = StringField(required=False)
    root_command_type = StringField(choices=BrewtilsCommand.COMMAND_TYPES)

    meta = {
        "queryset_class": FileFieldHandlingQuerySet,
        "auto_create_index": False,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [
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
        ],
    }


class Subscriber(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Subscriber

    garden = StringField()
    namespace = StringField()
    system = StringField()
    version = StringField()
    instance = StringField()
    command = StringField()
    subscriber_type = StringField()
    consumer_count = IntField(default=0)


class Topic(MongoModel, Document):
    brewtils_model = brewtils.models.Topic

    name = StringField(required=True)
    subscribers = EmbeddedDocumentListField("Subscriber")
    publisher_count = IntField(default=0)

    meta = {
        "auto_create_index": True,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [{"name": "unique_index", "fields": ["name"], "unique": True}],
    }


class System(MongoModel, Document):
    brewtils_model = brewtils.models.System

    name = StringField(required=True)
    description = StringField()
    version = StringField(required=True)
    namespace = StringField(required=True)
    max_instances = IntField(default=-1)
    instances = EmbeddedDocumentListField("Instance")
    commands = EmbeddedDocumentListField("Command")
    icon_name = StringField()
    display_name = StringField()
    metadata = DictField()
    local = BooleanField(default=True)
    template = StringField()
    groups = ListField(field=StringField())
    prefix_topic = StringField()
    requires = ListField(field=StringField())
    requires_timeout = IntField(default=300)
    garden_name = StringField()

    meta = {
        "auto_create_index": False,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [
            {
                "name": "unique_index",
                "fields": ["namespace", "name", "version"],
                "unique": True,
            }
        ],
    }


class Event(MongoModel, Document):
    brewtils_model = brewtils.models.Event

    name = StringField(required=True)
    namespace = StringField(required=True)
    garden = StringField()
    payload = DictField()
    error = BooleanField()
    metadata = DictField()
    timestamp = DateTimeField()


class RequestTemplate(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.RequestTemplate

    for field_name, field_info in Request.TEMPLATE_FIELDS.items():
        locals()[field_name] = field_info["field"](**field_info["kwargs"])


class DateTrigger(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.DateTrigger

    run_date = DateTimeField(required=True)
    timezone = StringField(
        required=False, default="utc", chocies=zoneinfo.available_timezones()
    )


class IntervalTrigger(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.IntervalTrigger

    weeks = IntField(default=0)
    days = IntField(default=0)
    hours = IntField(default=0)
    minutes = IntField(default=0)
    seconds = IntField(default=0)
    start_date = DateTimeField(required=False)
    end_date = DateTimeField(required=False)
    timezone = StringField(
        required=False, default="utc", chocies=zoneinfo.available_timezones()
    )
    jitter = IntField(required=False)
    reschedule_on_finish = BooleanField(required=False, default=False)


class CronTrigger(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.CronTrigger

    year = StringField(default="*")
    month = StringField(default="1")
    day = StringField(default="1")
    week = StringField(default="*")
    day_of_week = StringField(default="*")
    hour = StringField(default="0")
    minute = StringField(default="0")
    second = StringField(default="0")
    start_date = DateTimeField(required=False)
    end_date = DateTimeField(required=False)
    timezone = StringField(
        required=False, default="utc", chocies=zoneinfo.available_timezones()
    )
    jitter = IntField(required=False)


class FileTrigger(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.FileTrigger

    path = StringField(required=True)
    pattern = StringField(required=False)
    recursive = BooleanField(default=False)
    create = BooleanField(default=False)
    modify = BooleanField(default=False)
    move = BooleanField(default=False)
    delete = BooleanField(default=False)


class Replication(MongoModel, Document):
    brewtils_model = brewtils.models.Replication

    replication_id = StringField(required=True)
    expires_at = DateTimeField(required=True)

    meta = {
        "indexes": [
            {
                "name": "expires_at_index",
                "fields": ["expires_at"],
                "expireAfterSeconds": 0,
            },
        ],
    }


class Job(MongoModel, Document):
    brewtils_model = brewtils.models.Job

    meta = {
        "auto_create_index": False,
        "index_background": True,
        "indexes": [
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
        ],
    }

    TRIGGER_MODEL_MAPPING = {
        "date": DateTrigger,
        "cron": CronTrigger,
        "interval": IntervalTrigger,
        "file": FileTrigger,
    }

    name = StringField(required=True)
    trigger_type = StringField(required=True, choices=BrewtilsJob.TRIGGER_TYPES)
    trigger = GenericEmbeddedDocumentField(choices=list(TRIGGER_MODEL_MAPPING.values()))
    request_template = EmbeddedDocumentField("RequestTemplate", required=True)
    misfire_grace_time = IntField()
    coalesce = BooleanField(default=True)
    next_run_time = DateTimeField()
    success_count = IntField(required=True, default=0, min_value=0)
    error_count = IntField(required=True, default=0, min_value=0)
    skip_count = IntField(required=True, default=0, min_value=0)
    canceled_count = IntField(required=True, default=0, min_value=0)
    status = StringField(
        required=True, choices=BrewtilsJob.STATUS_TYPES, default="RUNNING"
    )
    max_instances = IntField(default=3, min_value=1)
    timeout = IntField()


class Connection(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Connection

    api = StringField(required=True)
    status = StringField(default="UNKOWN")
    status_info = EmbeddedDocumentField("StatusInfo")
    config = DictField()


class Garden(MongoModel, Document):
    brewtils_model = brewtils.models.Garden

    name = StringField(required=True, default="default")

    connection_type = StringField(required=False)
    receiving_connections = EmbeddedDocumentListField("Connection")
    publishing_connections = EmbeddedDocumentListField("Connection")

    systems = DummyField(required=False)

    parent = StringField(required=False)

    children = DummyField(required=False)
    has_parent = BooleanField(required=False, default=False)

    default_user = StringField(required=False)
    shared_users = BooleanField(required=False, default=False)

    metadata = DictField()

    version = StringField(required=True, default="0.0.0")

    meta = {
        "auto_create_index": False,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [
            {"name": "unique_index", "fields": ["name"], "unique": True},
            {
                "name": "local_unique_index",
                "fields": ["connection_type"],
                "unique": True,
                "partialFilterExpression": {"connection_type": "LOCAL"},
            },
        ],
    }


class File(MongoModel, Document):
    brewtils_model = brewtils.models.File

    owner_id = StringField(required=False)
    owner_type = StringField(required=False)
    updated_at = DateTimeField(default=get_current_time, required=True)
    file_name = StringField(required=True)
    file_size = IntField(required=True)
    chunks = DictField(required=False)
    chunk_size = IntField(required=True)
    md5_sum = StringField(required=False)

    # Dummy fields are here to handle legacy model. Can be removed once brewtils is updated
    # This prevents the models from getting accidentally saved in the database.
    owner = DummyField()
    request = DummyField()
    job = DummyField()

    # TTL Fields
    status = StringField()
    created_at = DateTimeField(default=get_current_time, required=True)
    root_command_type = StringField()


class FileChunk(MongoModel, Document):
    brewtils_model = brewtils.models.FileChunk

    file_id = StringField(required=True)
    offset = IntField(required=True)
    data = StringField(required=True)

    owner_type = StringField(required=False)
    owner = DummyField()

    # TTL Fields
    status = StringField()
    created_at = DateTimeField(default=get_current_time, required=True)
    updated_at = DateTimeField(default=get_current_time, required=True)
    root_command_type = StringField()


class Role(MongoModel, Document):
    brewtils_model = brewtils.models.Role

    name = StringField()
    description = StringField()
    permission = StringField()
    scope_gardens = ListField(field=StringField())
    scope_namespaces = ListField(field=StringField())
    scope_systems = ListField(field=StringField())
    scope_instances = ListField(field=StringField())
    scope_versions = ListField(field=StringField())
    scope_commands = ListField(field=StringField())

    protected = BooleanField(default=False)
    file_generated = BooleanField(required=True, default=False)

    meta = {
        "indexes": [{"name": "unique_index", "fields": ["name"], "unique": True}],
    }

    def __str__(self) -> str:
        return self.name


class UpstreamRole(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.UpstreamRole

    name = StringField()
    description = StringField()
    permission = StringField()
    scope_gardens = ListField(field=StringField())
    scope_namespaces = ListField(field=StringField())
    scope_systems = ListField(field=StringField())
    scope_instances = ListField(field=StringField())
    scope_versions = ListField(field=StringField())
    scope_commands = ListField(field=StringField())

    protected = BooleanField(default=False)
    file_generated = BooleanField(required=True, default=False)

    def __str__(self) -> str:
        return self.name


class AliasUserMap(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.AliasUserMap

    target_garden = StringField()
    username = StringField()


class User(MongoModel, Document):
    brewtils_model = brewtils.models.User

    username = StringField(required=True)
    password = StringField()
    roles = ListField(field=StringField())
    local_roles = DummyField(required=False)
    upstream_roles = EmbeddedDocumentListField("UpstreamRole")
    is_remote = BooleanField(required=True, default=False)
    user_alias_mapping = EmbeddedDocumentListField("AliasUserMap")
    metadata = DictField()
    protected = BooleanField(required=True, default=False)
    file_generated = BooleanField(required=True, default=False)
    preferences = DictField()

    meta = {
        "indexes": [{"name": "unique_index", "fields": ["username"], "unique": True}],
    }

    # _permissions_cache: Optional[dict] = None

    def __str__(self) -> str:
        return self.username


class UserToken(MongoModel, Document):
    brewtils_model = brewtils.models.UserToken

    issued_at = DateTimeField(required=True, default=get_current_time)
    expires_at = DateTimeField(required=True)
    username = StringField()
    uuid = StringField()

    meta = {
        "indexes": [
            {"name": "username_index", "fields": ["username"]},
            {"name": "uuid_index", "fields": ["uuid"]},
            {
                "name": "expires_at_index",
                "fields": ["expires_at"],
                "expireAfterSeconds": 0,
            },
        ]
    }


class Configuration(Document):
    # This is a snapshot of the configuration file last loaded
    # and is reset after migrations are completed. It should not
    # be used for optional configuration.
    action_ttl = IntField(default=-1)
    info_ttl = IntField(default=15)
    file_ttl = IntField(default=15)
    version = StringField(default="0.0.0")
