# -*- coding: utf-8 -*-
import datetime
import logging

import pytz
import six
import sys

try:
    from lark import ParseError
    from lark.exceptions import LarkError
except ImportError:
    from lark.common import ParseError

    LarkError = ParseError
from bson.objectid import ObjectId
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
    ReferenceField,
    StringField,
    FileField,
    CASCADE,
    PULL,
)
from mongoengine.errors import DoesNotExist

import brewtils.models
from .fields import DummyField, StatusInfo
from brewtils.choices import parse
from brewtils.errors import ModelValidationError, RequestStatusTransitionError
from brewtils.models import (
    Command as BrewtilsCommand,
    Instance as BrewtilsInstance,
    Parameter as BrewtilsParameter,
    Request as BrewtilsRequest,
    Job as BrewtilsJob,
)

__all__ = [
    "System",
    "Instance",
    "Command",
    "Parameter",
    "Request",
    "Choices",
    "Event",
    "Principal",
    "Role",
    "RefreshToken",
    "Job",
    "RequestTemplate",
    "DateTrigger",
    "CronTrigger",
    "IntervalTrigger",
    "FileTrigger",
    "Garden",
]


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

    def __init__(self, *args, **kwargs):
        EmbeddedDocument.__init__(self, *args, **kwargs)

    def clean(self):
        if self.type == "static" and not isinstance(self.value, (list, dict)):
            raise ModelValidationError(
                f"Can not save choices '{self}': type is 'static' but the value is "
                f"not a list or dictionary"
            )
        elif self.type == "url" and not isinstance(self.value, six.string_types):
            raise ModelValidationError(
                f"Can not save choices '{self}': type is 'url' but the value is "
                f"not a string"
            )
        elif self.type == "command" and not isinstance(
            self.value, (six.string_types, dict)
        ):
            raise ModelValidationError(
                f"Can not save choices '{self}': type is 'command' but the value is "
                f"not a string or dict"
            )

        if self.type == "command" and isinstance(self.value, dict):
            value_keys = self.value.keys()
            for required_key in ("command", "system", "version"):
                if required_key not in value_keys:
                    raise ModelValidationError(
                        f"Can not save choices '{self}': specifying value as a "
                        f"dictionary requires a '{required_key}' item"
                    )

        try:
            if self.details == {}:
                if isinstance(self.value, six.string_types):
                    self.details = parse(self.value)
                elif isinstance(self.value, dict):
                    self.details = parse(self.value["command"])
        except (LarkError, ParseError):
            raise ModelValidationError(
                f"Can not save choices '{self}': Unable to parse"
            )


class Parameter(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Parameter

    key = StringField(required=True)
    type = StringField(required=True, default="Any", choices=BrewtilsParameter.TYPES)
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

    # If no display name was set, it will default it to the same thing as the key
    def __init__(self, *args, **kwargs):
        if not kwargs.get("display_name", None):
            kwargs["display_name"] = kwargs.get("key", None)

        EmbeddedDocument.__init__(self, *args, **kwargs)

    def clean(self):
        """Validate before saving to the database"""

        if not self.nullable and self.optional and self.default is None:
            raise ModelValidationError(
                f"Can not save Parameter {self}: For this Parameter nulls are not "
                f"allowed, but the parameter is optional with no default defined."
            )

        if len(self.parameters) != len(
            set(parameter.key for parameter in self.parameters)
        ):
            raise ModelValidationError(
                f"Can not save Parameter {self}: Contains Parameters with duplicate keys"
            )


class Command(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Command

    name = StringField(required=True)
    description = StringField()
    parameters = EmbeddedDocumentListField("Parameter")
    command_type = StringField(choices=BrewtilsCommand.COMMAND_TYPES, default="ACTION")
    output_type = StringField(choices=BrewtilsCommand.OUTPUT_TYPES, default="STRING")
    schema = DictField()
    form = DictField()
    template = StringField()
    hidden = BooleanField()
    icon_name = StringField()

    def clean(self):
        """Validate before saving to the database"""

        if not self.name:
            raise ModelValidationError("Can not save a Command with an empty name")

        if self.command_type not in BrewtilsCommand.COMMAND_TYPES:
            raise ModelValidationError(
                f"Can not save Command {self}: Invalid command type '{self.command_type}'"
            )

        if self.output_type not in BrewtilsCommand.OUTPUT_TYPES:
            raise ModelValidationError(
                f"Can not save Command {self}: Invalid output type '{self.output_type}'"
            )

        if len(self.parameters) != len(
            set(parameter.key for parameter in self.parameters)
        ):
            raise ModelValidationError(
                f"Can not save Command {self}: Contains Parameters with duplicate keys"
            )


class Instance(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Instance

    id = ObjectIdField(required=True, default=ObjectId, unique=True, primary_key=True)
    name = StringField(required=True, default="default")
    description = StringField()
    status = StringField(default="INITIALIZING")
    status_info = EmbeddedDocumentField("StatusInfo", default=StatusInfo())
    queue_type = StringField()
    queue_info = DictField()
    icon_name = StringField()
    metadata = DictField()

    def clean(self):
        """Validate before saving to the database"""

        if self.status not in BrewtilsInstance.INSTANCE_STATUSES:
            raise ModelValidationError(
                f"Can not save Instance {self}: Invalid status '{self.status}'"
            )


class Request(MongoModel, Document):
    brewtils_model = brewtils.models.Request

    # These fields are duplicated for job types, changes to this field
    # necessitate a change to the RequestTemplateSchema in brewtils.
    TEMPLATE_FIELDS = {
        "system": {"field": StringField, "kwargs": {"required": True}},
        "system_version": {"field": StringField, "kwargs": {"required": True}},
        "instance_name": {"field": StringField, "kwargs": {"required": True}},
        "namespace": {"field": StringField, "kwargs": {"required": True}},
        "command": {"field": StringField, "kwargs": {"required": True}},
        "command_type": {"field": StringField, "kwargs": {}},
        "parameters": {"field": DictField, "kwargs": {}},
        "comment": {"field": StringField, "kwargs": {"required": False}},
        "metadata": {"field": DictField, "kwargs": {}},
        "output_type": {"field": StringField, "kwargs": {}},
    }

    for field_name, field_info in TEMPLATE_FIELDS.items():
        locals()[field_name] = field_info["field"](**field_info["kwargs"])

    parent = ReferenceField(
        "Request", dbref=True, required=False, reverse_delete_rule=CASCADE
    )
    children = DummyField(required=False)
    output = StringField()
    output_gridfs = FileField()
    output_type = StringField(choices=BrewtilsCommand.OUTPUT_TYPES)
    status = StringField(choices=BrewtilsRequest.STATUS_LIST, default="CREATED")
    command_type = StringField(choices=BrewtilsCommand.COMMAND_TYPES)
    created_at = DateTimeField(default=datetime.datetime.utcnow, required=True)
    updated_at = DateTimeField(default=None, required=True)
    error_class = StringField(required=False)
    has_parent = BooleanField(required=False)
    requester = StringField(required=False)

    meta = {
        "auto_create_index": False,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [
            # These are used for sorting all requests
            {"name": "command_index", "fields": ["command"]},
            {"name": "command_type_index", "fields": ["command_type"]},
            {"name": "system_index", "fields": ["system"]},
            {"name": "instance_name_index", "fields": ["instance_name"]},
            {"name": "namespace_index", "fields": ["namespace"]},
            {"name": "status_index", "fields": ["status"]},
            {"name": "created_at_index", "fields": ["created_at"]},
            {"name": "updated_at_index", "fields": ["updated_at"]},
            {"name": "comment_index", "fields": ["comment"]},
            {"name": "parent_ref_index", "fields": ["parent"]},
            {"name": "parent_index", "fields": ["has_parent"]},
            # These are for sorting parent requests
            {"name": "parent_command_index", "fields": ["has_parent", "command"]},
            {"name": "parent_system_index", "fields": ["has_parent", "system"]},
            {
                "name": "parent_instance_name_index",
                "fields": ["has_parent", "instance_name"],
            },
            {"name": "parent_status_index", "fields": ["has_parent", "status"]},
            {"name": "parent_created_at_index", "fields": ["has_parent", "created_at"]},
            {"name": "parent_comment_index", "fields": ["has_parent", "comment"]},
            # These are used for filtering all requests while sorting on created time
            {"name": "created_at_command_index", "fields": ["-created_at", "command"]},
            {"name": "created_at_system_index", "fields": ["-created_at", "system"]},
            {
                "name": "created_at_instance_name_index",
                "fields": ["-created_at", "instance_name"],
            },
            {"name": "created_at_status_index", "fields": ["-created_at", "status"]},
            # These are used for filtering parent while sorting on created time
            {
                "name": "parent_created_at_command_index",
                "fields": ["has_parent", "-created_at", "command"],
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
            # This is used for text searching
            {
                "name": "text_index",
                "fields": [
                    "$system",
                    "$command",
                    "$command_type",
                    "$comment",
                    "$status",
                    "$instance_name",
                ],
            },
        ],
    }

    logger = logging.getLogger(__name__)

    def pre_serialize(self):
        """If string output was over 16MB it was spilled over to the GridFS storage solution"""
        if self.output_gridfs:
            self.output = self.output_gridfs.read().decode("utf-8")
            self.output_gridfs = None

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.utcnow()

        # If the output size is too large, we switch it over
        # Max size for Mongo is 16MB, switching over at 15MB to be safe
        if self.output and sys.getsizeof(self.output) > (1000000 * 15):
            self.output_gridfs.put(self.output, encoding="utf-8")
            self.output = None

        super(Request, self).save(*args, **kwargs)

    def clean(self):
        """Validate before saving to the database"""

        if self.status not in BrewtilsRequest.STATUS_LIST:
            raise ModelValidationError(
                f"Can not save Request {self}: Invalid status '{self.status}'"
            )

        if (
            self.command_type is not None
            and self.command_type not in BrewtilsRequest.COMMAND_TYPES
        ):
            raise ModelValidationError(
                f"Can not save Request {self}: Invalid command type '{self.command_type}'"
            )

        if (
            self.output_type is not None
            and self.output_type not in BrewtilsRequest.OUTPUT_TYPES
        ):
            raise ModelValidationError(
                f"Can not save Request {self}: Invalid output type '{self.output_type}'"
            )

    def clean_update(self):
        """Ensure that the update would not result in an illegal status transition"""
        # Get the original status
        old_status = Request.objects.get(id=self.id).status

        if self.status != old_status:
            if old_status in BrewtilsRequest.COMPLETED_STATUSES:
                raise RequestStatusTransitionError(
                    f"Status for a request cannot be updated once it has been "
                    f"completed. Current: {old_status}, Requested: {self.status}"
                )

            if (
                old_status == "IN_PROGRESS"
                and self.status not in BrewtilsRequest.COMPLETED_STATUSES
            ):
                raise RequestStatusTransitionError(
                    f"Request status can only transition from IN_PROGRESS to a "
                    f"completed status. Requested: {self.status}, completed statuses "
                    f"are {BrewtilsRequest.COMPLETED_STATUSES}."
                )


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

    def clean(self):
        """Validate before saving to the database"""

        if len(self.instances) > self.max_instances > -1:
            raise ModelValidationError(
                "Can not save System %s: Number of instances (%s) "
                "exceeds system limit (%s)"
                % (str(self), len(self.instances), self.max_instances)
            )

        if len(self.instances) != len(
            set(instance.name for instance in self.instances)
        ):
            raise ModelValidationError(
                "Can not save System %s: Duplicate instance names" % str(self)
            )


class Event(MongoModel, Document):
    brewtils_model = brewtils.models.Event

    name = StringField(required=True)
    namespace = StringField(required=True)
    garden = StringField()
    payload = DictField()
    error = BooleanField()
    metadata = DictField()
    timestamp = DateTimeField()


class Role(MongoModel, Document):
    brewtils_model = brewtils.models.Role

    name = StringField(required=True)
    description = StringField()
    permissions = ListField(field=StringField())

    meta = {
        "auto_create_index": False,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [{"name": "unique_index", "fields": ["name"], "unique": True}],
    }


class Principal(MongoModel, Document):
    brewtils_model = brewtils.models.Principal

    username = StringField(required=True)
    hash = StringField()
    roles = ListField(field=ReferenceField("Role", reverse_delete_rule=PULL))
    preferences = DictField()
    metadata = DictField()

    meta = {
        "auto_create_index": False,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [{"name": "unique_index", "fields": ["username"], "unique": True}],
    }


class RefreshToken(Document):
    brewtils_model = brewtils.models.RefreshToken

    issued = DateTimeField(required=True)
    expires = DateTimeField(required=True)
    payload = DictField(required=True)

    meta = {"indexes": [{"fields": ["expires"], "expireAfterSeconds": 0}]}

    def get_principal(self):
        principal_id = self.payload.get("sub")
        if not principal_id:
            return None

        try:
            return Principal.objects.get(id=principal_id)
        except DoesNotExist:
            return None


class RequestTemplate(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.RequestTemplate

    for field_name, field_info in Request.TEMPLATE_FIELDS.items():
        locals()[field_name] = field_info["field"](**field_info["kwargs"])


class DateTrigger(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.DateTrigger

    run_date = DateTimeField(required=True)
    timezone = StringField(required=False, default="utc", chocies=pytz.all_timezones)


class IntervalTrigger(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.IntervalTrigger

    weeks = IntField(default=0)
    days = IntField(default=0)
    hours = IntField(default=0)
    minutes = IntField(default=0)
    seconds = IntField(default=0)
    start_date = DateTimeField(required=False)
    end_date = DateTimeField(required=False)
    timezone = StringField(required=False, default="utc", chocies=pytz.all_timezones)
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
    timezone = StringField(required=False, default="utc", chocies=pytz.all_timezones)
    jitter = IntField(required=False)


class FileTrigger(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.FileTrigger

    pattern = ListField()
    path = StringField(default=".")
    recursive = BooleanField(default=False)
    callbacks = DictField()

    def clean(self):
        """Validate before saving to the database"""
        if not list(filter(lambda i: i != "", self.pattern)):
            raise ModelValidationError(
                "Cannot save FileTrigger. Must have at least one non-empty pattern."
            )

        if True not in self.callbacks.values():
            raise ModelValidationError(
                "Cannot save FileTrigger. Must have at least one callback selected."
            )


class Job(MongoModel, Document):
    brewtils_model = brewtils.models.Job

    meta = {
        "auto_create_index": False,
        "index_background": True,
        "indexes": [
            {"name": "next_run_time_index", "fields": ["next_run_time"], "sparse": True}
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
    status = StringField(
        required=True, choices=BrewtilsJob.STATUS_TYPES, default="RUNNING"
    )
    max_instances = IntField(default=3, min_value=1)

    def clean(self):
        """Validate before saving to the database"""

        if self.trigger_type not in self.TRIGGER_MODEL_MAPPING:
            raise ModelValidationError(
                f"Cannot save job. No mongo model for trigger type {self.trigger_type}"
            )

        trigger_class = self.TRIGGER_MODEL_MAPPING.get(self.trigger_type)
        if not isinstance(self.trigger, trigger_class):
            raise ModelValidationError(
                f"Cannot save job. Expected trigger type {self.trigger_type} but "
                f"actual type was {type(self.trigger)}"
            )


class Garden(MongoModel, Document):
    brewtils_model = brewtils.models.Garden

    name = StringField(required=True, default="default")
    status = StringField(default="INITIALIZING")
    status_info = EmbeddedDocumentField("StatusInfo", default=StatusInfo())
    namespaces = ListField()
    connection_type = StringField()
    connection_params = DictField()
    systems = ListField(ReferenceField(System, reverse_delete_rule=PULL))

    meta = {
        "auto_create_index": False,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [{"name": "unique_index", "fields": ["name"], "unique": True}],
    }

    def deep_save(self):
        for system in self.systems:
            system.save()

        self.save()


class SystemGardenMapping(MongoModel, Document):
    system = ReferenceField("System")
    garden = ReferenceField("Garden")
