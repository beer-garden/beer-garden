# -*- coding: utf-8 -*-
import datetime
import json
import logging

import pytz
import six
from passlib.apps import custom_app_context

try:
    from lark import ParseError
    from lark.exceptions import LarkError
except ImportError:
    from lark.common import ParseError

    LarkError = ParseError
from operator import attrgetter
from typing import Optional, Tuple

import brewtils.models
from brewtils.choices import parse
from brewtils.errors import ModelValidationError, RequestStatusTransitionError
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import Job as BrewtilsJob
from brewtils.models import Parameter as BrewtilsParameter
from brewtils.models import Request as BrewtilsRequest
from bson.objectid import ObjectId
from mongoengine import (
    CASCADE,
    NULLIFY,
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
    LazyReferenceField,
    ListField,
    ObjectIdField,
    ReferenceField,
    StringField,
)
from mongoengine.errors import DoesNotExist

from .fields import DummyField, StatusInfo
from .validators import validate_permissions

__all__ = [
    "System",
    "Instance",
    "Command",
    "Parameter",
    "Request",
    "Choices",
    "Event",
    "Principal",
    "LegacyRole",
    "RefreshToken",
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
    "RoleAssignment",
    "User",
]

REQUEST_MAX_PARAM_SIZE = 5 * 1_000_000


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
                "not a list or dictionary"
            )
        elif self.type == "url" and not isinstance(self.value, six.string_types):
            raise ModelValidationError(
                f"Can not save choices '{self}': type is 'url' but the value is "
                "not a string"
            )
        elif self.type == "command" and not isinstance(
            self.value, (six.string_types, dict)
        ):
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
        "namespace": {"field": StringField, "kwargs": {"required": False}},
        "command": {"field": StringField, "kwargs": {"required": True}},
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
    hidden = BooleanField(required=False)
    requester = StringField(required=False)
    parameters_gridfs = FileField()

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
            # These are used for filtering hidden while sorting on created time
            # I THINK this makes the set of indexes above superfluous, but I'm keeping
            # both as a safety measure
            {
                "name": "hidden_parent_created_at_command_index",
                "fields": ["hidden", "has_parent", "-created_at", "command"],
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
        """Pull any fields out of GridFS"""
        encoding = "utf-8"

        if self.output_gridfs:
            self.logger.debug("Retrieving output from GridFS")
            self.output = self.output_gridfs.read().decode(encoding)
            self.output_gridfs = None

        if self.parameters_gridfs:
            self.logger.debug("Retrieving parameters from GridFS")
            self.parameters = json.loads(self.parameters_gridfs.read().decode(encoding))
            self.parameters_gridfs = None

    def save(self, *args, **kwargs):
        """Save a request, moving request attributes to GridFS if too big"""
        self.updated_at = datetime.datetime.utcnow()
        encoding = "utf-8"

        if self.parameters:
            params_json = json.dumps(self.parameters)
            if len(params_json) > REQUEST_MAX_PARAM_SIZE:
                self.logger.debug("Parameters too bg, storing in GridFS")
                self.parameters_gridfs.put(params_json, encoding=encoding)
                self.parameters = None

        if self.output:
            output_json = json.dumps(self.output)
            if len(output_json) > REQUEST_MAX_PARAM_SIZE:
                self.logger.info("Output size too big, storing in gridfs")
                self.output_gridfs.put(output_json, encoding=encoding)
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
                f"Can not save Request {self}: Invalid command type"
                f" '{self.command_type}'"
            )

        if (
            self.output_type is not None
            and self.output_type not in BrewtilsRequest.OUTPUT_TYPES
        ):
            raise ModelValidationError(
                f"Can not save Request {self}: Invalid output type '{self.output_type}'"
            )

        # Deal with has_parent
        if self.has_parent is None:
            self.has_parent = bool(self.parent)
        elif self.has_parent != bool(self.parent):
            raise ModelValidationError(
                f"Cannot save Request {self}: parent value of {self.parent!r} is not "
                f"consistent with has_parent value of {self.has_parent}"
            )

    def clean_update(self):
        """Ensure that the update would not result in an illegal status transition"""
        # Get the original status
        old_status = Request.objects.get(id=self.id).status

        if self.status != old_status:
            if old_status in BrewtilsRequest.COMPLETED_STATUSES:
                raise RequestStatusTransitionError(
                    "Status for a request cannot be updated once it has been "
                    f"completed. Current: {old_status}, Requested: {self.status}"
                )

            if (
                old_status == "IN_PROGRESS"
                and self.status not in BrewtilsRequest.COMPLETED_STATUSES
            ):
                raise RequestStatusTransitionError(
                    "Request status can only transition from IN_PROGRESS to a "
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
    template = StringField()

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


class LegacyRole(MongoModel, Document):
    brewtils_model = brewtils.models.LegacyRole

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
    roles = ListField(field=ReferenceField("LegacyRole", reverse_delete_rule=PULL))
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
        if self.connection_type != "LOCAL":
            self._update_associated_systems()

        self.save()

    def _update_associated_systems(self):
        """If the call to the `deep_save` method is on a child garden object, we ensure
        that when saving the systems, unknowns are deleted."""
        # import moved here to avoid a circular import loop
        from beer_garden.systems import get_systems, remove_system

        logger = logging.getLogger(self.__class__.__name__)

        def _get_system_triple(system: System) -> Tuple[str, str, str]:
            return (
                system.namespace,
                system.name,
                system.version,
            )

        our_namespaces = set(self.namespaces).union(
            set(map(attrgetter("namespace"), self.systems))
        )
        # we leverage the fact that systems must be unique up to the triple of their
        # namespaces, names and versions
        child_systems_already_known = {
            _get_system_triple(system): str(system.id)
            for system in get_systems(
                filter_params={"local": False, "namespace__in": our_namespaces}
            )
        }

        for system in self.systems:
            triple = _get_system_triple(system)

            if triple in child_systems_already_known:
                system_id_to_remove = child_systems_already_known.pop(triple)

                if system_id_to_remove != str(system.id):
                    # remove the system from before this update with the same triple
                    logger.debug(
                        f"Removing System <{triple[0]}"
                        f", {triple[1]}"
                        f", {triple[2]}> with ID={system_id_to_remove}"
                        f"; doesn't match ID={str(system.id)}"
                        " for known system with same attributes"
                    )
                    remove_system(system_id=system_id_to_remove)

            system.save()

        # if there's anything left over, delete those too; this could occur, e.g.,
        # if a child system deleted a particular version of a plugin and installed
        # another version of the same plugin
        for bad_system_id in child_systems_already_known.values():
            logger.debug(
                f"Removing System with ID={str(bad_system_id)} because it "
                f"matches no known system in child garden ({self.name})"
            )
            remove_system(system_id=bad_system_id)


class SystemGardenMapping(MongoModel, Document):
    system = ReferenceField("System")
    garden = ReferenceField("Garden")


class File(MongoModel, Document):
    brewtils_model = brewtils.models.File

    owner_id = StringField(required=False)
    owner_type = StringField(required=False)
    request = LazyReferenceField(Request, required=False, reverse_delete_rule=NULLIFY)
    job = LazyReferenceField(Job, required=False, reverse_delete_rule=NULLIFY)
    updated_at = DateTimeField(default=datetime.datetime.utcnow, required=True)
    file_name = StringField(required=True)
    file_size = IntField(required=True)
    chunks = DictField(required=False)
    chunk_size = IntField(required=True)

    # This was originally used instead of request and job. See #833
    # We could probably have kept using this if a GenericLazyReferenceField could have
    # a reverse_delete_rule. Alas!
    owner = DummyField()


class FileChunk(MongoModel, Document):
    brewtils_model = brewtils.models.FileChunk

    file_id = StringField(required=True)
    offset = IntField(required=True)
    data = StringField(required=True)
    # Delete Rule (2) = CASCADE; This causes this document to be deleted when the owner doc is.
    owner = LazyReferenceField(File, required=False, reverse_delete_rule=CASCADE)


class RawFile(Document):
    file = FileField()


class Role(Document):
    name = StringField()
    description = StringField()
    permissions = ListField(field=StringField(), validation=validate_permissions)

    meta = {
        "indexes": [{"name": "unique_index", "fields": ["name"], "unique": True}],
    }


class RoleAssignmentDomain(EmbeddedDocument):
    scope = StringField(required=True, choices=["Garden", "System", "Command"])
    identifiers = DictField(required=True)


class RoleAssignment(EmbeddedDocument):
    domain = EmbeddedDocumentField(RoleAssignmentDomain)
    role = ReferenceField("Role")


class User(Document):
    username = StringField(required=True)
    password = StringField()
    role_assignments = EmbeddedDocumentListField("RoleAssignment")

    meta = {
        "indexes": [{"name": "unique_index", "fields": ["username"], "unique": True}],
    }

    _permissions_cache: Optional[dict] = None

    @property
    def permissions(self) -> dict:
        """Return the user's permissions organized by permission name. This is
        calculated via beer_garden.authorization.permissions_for_user and is cached on
        the User object to avoid unnecessary recalculation.

        Returns:
            dict: The user's permissions organized by permission name
        """
        from beer_garden.authorization import permissions_for_user

        if self._permissions_cache is None:
            self._permissions_cache = permissions_for_user(self)

        return self._permissions_cache

    def clear_permissions_cache(self) -> None:
        """Clear the cached permission set for the user. This is useful if the user's
        role assignments have been changed and you want to perform a permission check
        using those new role assignments without reloading the entire user object.
        """
        self._permissions_cache = None

    def set_permissions_cache(self, permissions: dict) -> None:
        """Manually set the cached permission set for the user. This cache is typically
        set and checked by the permissions property method. In cases where those
        permissions are externally sourced (such as an access token in a web request
        that was provided via initial authentication), this method can be used to
        manually set the _permissions_cache value so that subsequent calls to
        permissions related helper functions do not unnecessarily recalculate the user
        permissions.

        Args:
            permissions: A dictionary containing the user's permissions. The format
                should match the one produced by permissions_for_user in
                beer_garden.authorization

        Returns:
            None
        """
        self._permissions_cache = permissions

    def set_password(self, password: str):
        """This helper should be used to set the user's password, rather than directly
        assigning a value. This ensures that the password is stored as a hash rather
        than in plain text

        Args:
            password: String to set as the user's password.

        Returns:
            None
        """
        self.password = custom_app_context.hash(password)

    def verify_password(self, password: str):
        """Checks the provided plaintext password against thea user's stored password
        hash

        Args:
            password: Plaintext string to check against user's password"

        Returns:
            bool: True if the password matches, False otherwise
        """
        return custom_app_context.verify(password, self.password)
