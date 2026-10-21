# -*- coding: utf-8 -*-
import datetime
import logging
import zoneinfo
from typing import Tuple

import brewtils.models
from brewtils.choices import parse
from brewtils.errors import ModelValidationError
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import Job as BrewtilsJob
from brewtils.models import Parameter as BrewtilsParameter
from brewtils.models import Request as BrewtilsRequest
from brewtils.models import System as BrewtilsSystem
from lark import ParseError
from lark.exceptions import LarkError
from mongoengine import (
    PULL,
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    DynamicField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    FileField,
    GenericEmbeddedDocumentField,
    IntField,
    ListField,
    ObjectIdField,
    ReferenceField,
    StringField,
)
from mongoengine.errors import DoesNotExist

from beer_garden import config
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

    def __init__(self, *args, **kwargs):
        EmbeddedDocument.__init__(self, *args, **kwargs)

    def clean(self):
        if self.type == "static" and not isinstance(self.value, (list, dict)):
            raise ModelValidationError(
                f"Can not save choices '{self}': type is 'static' but the value is "
                "not a list or dictionary"
            )
        elif self.type == "url" and not isinstance(self.value, str):
            raise ModelValidationError(
                f"Can not save choices '{self}': type is 'url' but the value is "
                "not a string"
            )
        elif self.type == "command" and not isinstance(self.value, (str, dict)):
            raise ModelValidationError(
                f"Can not save choices '{self}': type is 'command' but the value is "
                "not a string or dict"
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
                if isinstance(self.value, str):
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
                "allowed, but the parameter is optional with no default defined."
            )

        if len(self.parameters) != len(
            set(parameter.key for parameter in self.parameters)
        ):
            raise ModelValidationError(
                f"Can not save Parameter {self}: Contains Parameters with duplicate"
                " keys"
            )


class Command(MongoModel, EmbeddedDocument):
    brewtils_model = brewtils.models.Command

    name = StringField(required=True)
    display_name = StringField()
    description = StringField()
    parameters = EmbeddedDocumentListField("Parameter")
    command_type = StringField(choices=BrewtilsCommand.COMMAND_TYPES, default="ACTION")
    output_type = StringField(choices=BrewtilsCommand.OUTPUT_TYPES, default="STRING")
    schema = DictField()
    form = DictField()
    template = StringField()
    hidden = BooleanField()
    icon_name = StringField()
    metadata = DictField()
    tags = ListField(field=StringField())
    topics = ListField(field=StringField())
    allow_any_kwargs = BooleanField(default=False)

    def clean(self):
        """Validate before saving to the database"""

        if not self.name:
            raise ModelValidationError("Can not save a Command with an empty name")

        if self.command_type not in BrewtilsCommand.COMMAND_TYPES:
            raise ModelValidationError(
                f"Can not save Command {self}: Invalid command type"
                f" '{self.command_type}'"
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
    updated_at = DateTimeField(default=None, required=True)
    status_updated_at = DateTimeField()
    error_class = StringField(required=False)
    has_parent = BooleanField(required=False)
    hidden = BooleanField(required=False, default=False)
    requester = StringField(required=False)
    is_event = BooleanField(required=False)
    source_garden = StringField(required=False)
    target_garden = StringField(required=False)
    root_command_type = StringField(choices=BrewtilsCommand.COMMAND_TYPES)

    # output_gridfs = FileField()
    # parameters_gridfs = FileField()

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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.subscriber_type == other.subscriber_type
                and self.garden == other.garden
                and self.namespace == other.namespace
                and self.system == other.system
                and self.version == other.version
                and self.instance == other.instance
                and self.command == other.command
            )
        return False


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

    def add_subscriber(self, subscriber: Subscriber):
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)
            self.save()

    def remove_subscriber(self, subscriber: Subscriber):

        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
            self.save()


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

    def delete(self, **kwargs):

        try:
            if self.local and len(self.instances) > 0:
                for command in self.commands:
                    for instance in self.instances:
                        if len(command.topics) > 0:
                            for topic in command.topics:
                                if Topic.objects(name=topic).count() > 0:
                                    db_topic = Topic.objects.get(name=topic)

                                    for subscriber in db_topic.subscribers:
                                        if (
                                            subscriber.garden == self.garden_name
                                            and subscriber.system == self.name
                                            and subscriber.namespace == self.namespace
                                            and subscriber.version == self.version
                                            and subscriber.instance == instance.name
                                            and subscriber.command == command.name
                                            and subscriber.subscriber_type
                                            == "ANNOTATED"
                                        ):
                                            db_topic.remove_subscriber(subscriber)

                                    if len(db_topic.subscribers) == 0:
                                        db_topic.delete()

                        if not self.prefix_topic:
                            topic_generated = (
                                f"{self.garden_name}.{self.namespace}."
                                f"{self.name}.{self.version}."
                                f"{instance.name}.{command.name}"
                            )
                        else:
                            topic_generated = f"{self.prefix_topic}.{command.name}"

                        if Topic.objects(name=topic_generated).count() > 0:
                            db_topic = Topic.objects.get(name=topic_generated)

                            for subscriber in db_topic.subscribers:
                                if (
                                    subscriber.garden == self.garden_name
                                    and subscriber.system == self.name
                                    and subscriber.namespace == self.namespace
                                    and subscriber.version == self.version
                                    and subscriber.instance == instance.name
                                    and subscriber.command == command.name
                                    and subscriber.subscriber_type == "GENERATED"
                                ):
                                    db_topic.remove_subscriber(subscriber)

                            if len(db_topic.subscribers) == 0:
                                db_topic.delete()
        except DoesNotExist:
            logger.error(
                (
                    "Error finding garden for system deletion "
                    f"Namespace = {self.namespace} "
                    f"System {self.name} "
                    f"Version {self.version}"
                )
            )

        super().delete(**kwargs)

    def save(self, **kwargs):
        max_history = config.get("plugin.status_history", default=5)
        for instance in self.instances:
            if instance.status_info and len(instance.status_info.history) > max_history:
                instance.status_info.history = instance.status_info.history[
                    (max_history * -1) :
                ]

        if self.local:
            self.garden_name = config.get("garden.name")
            self.save_topics()

        return super().save(**kwargs)

    def update(self, **kwargs):

        if self.local:
            self.save_topics()

        return super().update(**kwargs)

    def modify(self, query=None, **update):

        is_updated = super().modify(query, **update)

        if (
            is_updated
            and self.local
            and ("commands" in update or "push_all__instances" in update)
        ):
            self.save_topics()

        return is_updated

    def save_topics(self):

        if not self.local:
            # Skip topic management for non-local systems,
            # as they won't have any topics to manage
            return

        if len(self.instances) > 0:
            for command in self.commands:
                for instance in self.instances:
                    if len(command.topics) > 0:
                        for topic in command.topics:
                            if Topic.objects(name=topic).count() > 0:
                                db_topic = Topic.objects.get(name=topic)
                            else:
                                db_topic = Topic(name=topic)

                            db_topic.add_subscriber(
                                Subscriber(
                                    garden=self.garden_name,
                                    namespace=self.namespace,
                                    system=self.name,
                                    version=self.version,
                                    instance=instance.name,
                                    command=command.name,
                                    subscriber_type="ANNOTATED",
                                )
                            )

                    if not self.prefix_topic:
                        topic_generated = (
                            f"{self.garden_name}.{self.namespace}."
                            f"{self.name}.{self.version}."
                            f"{instance.name}.{command.name}"
                        )
                    else:
                        topic_generated = f"{self.prefix_topic}.{command.name}"

                    if Topic.objects(name=topic_generated).count() > 0:
                        db_topic = Topic.objects.get(name=topic_generated)
                    else:
                        db_topic = Topic(name=topic_generated)

                        db_topic.add_subscriber(
                            Subscriber(
                                garden=self.garden_name,
                                namespace=self.namespace,
                                system=self.name,
                                version=self.version,
                                instance=instance.name,
                                command=command.name,
                                subscriber_type="GENERATED",
                            )
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

    systems = ListField(ReferenceField(System, reverse_delete_rule=PULL))

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

    def deep_save(self):
        max_history = config.get("garden.status_history", default=5)
        for connection in self.receiving_connections:
            if (
                connection.status_info
                and len(connection.status_info.history) > max_history
            ):
                connection.status_info.history = connection.status_info.history[
                    (max_history * -1) :
                ]

        for connection in self.publishing_connections:
            if (
                connection.status_info
                and len(connection.status_info.history) > max_history
            ):
                connection.status_info.history = connection.status_info.history[
                    (max_history * -1) :
                ]

        if self.connection_type != "LOCAL":
            self._update_associated_systems()

            # Ensure no configurations are stored locally, if sent
            if self.has_parent:
                for connection in self.receiving_connections:
                    connection.config = {}

                for connection in self.publishing_connections:
                    connection.config = {}

        self.save()

    def _update_associated_systems(self):
        """If the call to the `deep_save` method is on a child garden object, we ensure
        that when saving the systems, unknowns are deleted."""
        # import moved here to avoid a circular import loop
        from beer_garden.systems import remove_system

        def _get_system_triple(system: System) -> Tuple[str, str, str]:
            namespace = getattr(system, "namespace", self.name)
            name = getattr(system, "name", None)
            version = getattr(system, "version", None)
            if not name or not version:
                name = str(system)
                version = ""
            return (
                namespace,
                name,
                version,
            )

        # we leverage the fact that systems must be unique up to the triple of their
        # namespaces, names and versions
        child_systems_already_known = {}
        for system in System.objects(garden_name=self.name).only(
            "garden_name",
            "namespace",
            "name",
            "version",
            "prefix_topic",
            "instances.name",
            "commands.topics",
            "commands.name",
        ):
            child_systems_already_known[_get_system_triple(system)] = system.id

        local_systems = [
            _get_system_triple(system)
            for system in System.objects(local=True).only(
                "namespace", "name", "version"
            )
        ]

        for system in self.systems:
            triple = _get_system_triple(system)

            # Check is System is a Local System
            if triple not in local_systems:
                if triple in child_systems_already_known:
                    system_id_to_remove = child_systems_already_known.pop(triple)

                    # system_id_to_remove and system.id are ObjectIds
                    if system_id_to_remove != system.id:
                        # remove the system from before this update with the same triple
                        logger.error(
                            f"Removing System <{triple[0]}"
                            f", {triple[1]}"
                            f", {triple[2]}> with ID={system_id_to_remove}"
                            f"; doesn't match ID={system.id}"
                            " for known system with same attributes"
                        )
                        remove_system(system_id=system_id_to_remove)

                try:
                    system.garden_name = self.name
                    system.save()
                    system.save_topics()
                except Exception as ex:
                    logger.error(
                        f"Error saving system {str(system)} in garden {self.name}: {ex}"
                    )

            else:
                system.delete()

        # if there's anything left over, delete those too; this could occur, e.g.,
        # if a child system deleted a particular version of a plugin and installed
        # another version of the same plugin
        for bad_system_id in child_systems_already_known.values():
            logger.error(
                f"Removing System with ID={str(bad_system_id)} because it "
                f"matches no known system in child garden ({self.name})"
            )
            try:
                remove_system(system_id=bad_system_id)
            except Exception:
                remove_system(system=BrewtilsSystem(id=str(bad_system_id)))

        self.systems = System.objects(garden_name=self.name)


class SystemGardenMapping(MongoModel, Document):
    system = ReferenceField("System")
    garden = ReferenceField("Garden")


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

    # This was originally used instead of request and job. See #833
    # We could probably have kept using this if a GenericLazyReferenceField could have
    # a reverse_delete_rule. Alas!
    owner = DummyField()

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

    # TTL Fields
    status = StringField()
    created_at = DateTimeField(default=get_current_time, required=True)
    updated_at = DateTimeField(default=get_current_time, required=True)
    root_command_type = StringField()


class RawFile(Document):
    file = FileField()
    created_at = DateTimeField(default=get_current_time, required=True)
    request_id = StringField()

    # TTL Fields
    status = StringField()
    updated_at = DateTimeField(default=get_current_time, required=True)
    root_command_type = StringField()

    meta = {"queryset_class": FileFieldHandlingQuerySet}


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

    def clean(self):
        """Validate before saving to the database"""

        if self.permission not in brewtils.models.Role.PERMISSION_TYPES:
            raise ModelValidationError(
                f"Cannot save Role. No permission type {self.permission}"
            )


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

    def clean(self):
        """Validate before saving to the database"""

        if self.permission not in brewtils.models.Role.PERMISSION_TYPES:
            raise ModelValidationError(
                f"Cannot save Role. No permission type {self.permission}"
            )


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

    meta = {
        "indexes": [{"name": "unique_index", "fields": ["username"], "unique": True}],
    }

    # _permissions_cache: Optional[dict] = None

    def save(self, *args, **kwargs):
        if self.local_roles:
            for local_role in self.local_roles:
                if local_role.name not in self.roles:
                    self.roles.append(local_role.name)

        if self.roles:
            for role in self.roles:
                try:
                    Role.objects.get(name=role)
                except DoesNotExist:
                    raise ModelValidationError(f"Local Role '{role}' does not exist")

        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.username

    def delete(self, *args, **kwargs):
        try:
            UserToken.objects.get(username=self.username).delete()
        except DoesNotExist:
            pass
        return super().delete(*args, **kwargs)


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
