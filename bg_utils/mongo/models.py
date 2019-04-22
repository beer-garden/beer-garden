import copy
import logging

import datetime
import pytz
import six

try:
    from lark import ParseError
    from lark.exceptions import LarkError
except ImportError:
    from lark.common import ParseError

    LarkError = ParseError
from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    DynamicField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    GenericEmbeddedDocumentField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
    CASCADE,
    PULL,
)
from mongoengine.errors import DoesNotExist

from bg_utils.mongo.fields import DummyField, StatusInfo
from brewtils.choices import parse
from brewtils.errors import BrewmasterModelValidationError
from brewtils.models import (
    Choices as BrewtilsChoices,
    Command as BrewtilsCommand,
    Instance as BrewtilsInstance,
    Parameter as BrewtilsParameter,
    Request as BrewtilsRequest,
    System as BrewtilsSystem,
    Event as BrewtilsEvent,
    Principal as BrewtilsPrincipal,
    Role as BrewtilsRole,
    Job as BrewtilsJob,
    RequestTemplate as BrewtilsRequestTemplate,
    DateTrigger as BrewtilsDateTrigger,
    CronTrigger as BrewtilsCronTrigger,
    IntervalTrigger as BrewtilsIntervalTrigger,
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
]


# MongoEngine needs all EmbeddedDocuments to be defined before any Documents that reference them
# So Parameter must be defined before Command, and choices should be defined before Parameter


class Choices(EmbeddedDocument, BrewtilsChoices):
    display = StringField(required=True, choices=BrewtilsChoices.DISPLAYS)
    strict = BooleanField(required=True, default=True)
    type = StringField(required=True, default="static", choices=BrewtilsChoices.TYPES)
    value = DynamicField(required=True)
    details = DictField()

    def __init__(self, *args, **kwargs):
        EmbeddedDocument.__init__(self, *args, **kwargs)

    def __str__(self):
        return BrewtilsChoices.__str__(self)

    def __repr__(self):
        return BrewtilsChoices.__repr__(self)

    def clean(self):
        if self.type == "static" and not isinstance(self.value, (list, dict)):
            raise BrewmasterModelValidationError(
                "Error saving choices '%s' - type was 'static' "
                "but the value was not a list or dictionary" % self.value
            )
        elif self.type == "url" and not isinstance(self.value, six.string_types):
            raise BrewmasterModelValidationError(
                "Error saving choices '%s' - type was 'url' but "
                "the value was not a string" % self.value
            )
        elif self.type == "command" and not isinstance(
            self.value, (six.string_types, dict)
        ):
            raise BrewmasterModelValidationError(
                "Error saving choices '%s' - type was 'command' "
                "but the value was not a string or dict" % self.value
            )

        if self.type == "command" and isinstance(self.value, dict):
            value_keys = self.value.keys()
            for required_key in ("command", "system", "version"):
                if required_key not in value_keys:
                    raise BrewmasterModelValidationError(
                        "Error saving choices '%s' - specifying "
                        "value as a dictionary requires a '%s' "
                        "item" % (self.value, required_key)
                    )

        try:
            if self.details == {}:
                if isinstance(self.value, six.string_types):
                    self.details = parse(self.value)
                elif isinstance(self.value, dict):
                    self.details = parse(self.value["command"])
        except (LarkError, ParseError):
            raise BrewmasterModelValidationError(
                "Error saving choices '%s' - unable to parse" % self.value
            )


class Parameter(EmbeddedDocument, BrewtilsParameter):
    """Mongo-Backed BREWMASTER Parameter Object"""

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
    parameters = ListField(EmbeddedDocumentField("Parameter"))

    # If no display name was set, it will default it to the same thing as the key
    def __init__(self, *args, **kwargs):
        if not kwargs.get("display_name", None):
            kwargs["display_name"] = kwargs.get("key", None)

        EmbeddedDocument.__init__(self, *args, **kwargs)

    def __str__(self):
        return BrewtilsParameter.__str__(self)

    def __repr__(self):
        return BrewtilsParameter.__repr__(self)

    def clean(self):
        """Validate before saving to the database"""

        if not self.nullable and self.optional and self.default is None:
            raise BrewmasterModelValidationError(
                "Can not save Parameter %s: For this Parameter "
                "nulls are not allowed, but the parameter is "
                "optional with no default defined." % self.key
            )

        if len(self.parameters) != len(
            set(parameter.key for parameter in self.parameters)
        ):
            raise BrewmasterModelValidationError(
                "Can not save Parameter %s: Contains Parameters "
                "with duplicate keys" % self.key
            )


class Command(Document, BrewtilsCommand):
    """Mongo-Backed BREWMASTER Command Object"""

    name = StringField(required=True, unique_with="system")
    description = StringField()
    parameters = ListField(EmbeddedDocumentField("Parameter"))
    command_type = StringField(choices=BrewtilsCommand.COMMAND_TYPES, default="ACTION")
    output_type = StringField(choices=BrewtilsCommand.OUTPUT_TYPES, default="STRING")
    schema = DictField()
    form = DictField()
    template = StringField()
    icon_name = StringField()
    system = ReferenceField("System")

    def __str__(self):
        return BrewtilsCommand.__str__(self)

    def __repr__(self):
        return BrewtilsCommand.__repr__(self)

    def clean(self):
        """Validate before saving to the database"""

        if not self.name:
            raise BrewmasterModelValidationError(
                "Can not save Command%s: Empty name"
                % (" for system " + (self.system.name if self.system else ""))
            )

        if self.command_type not in BrewtilsCommand.COMMAND_TYPES:
            raise BrewmasterModelValidationError(
                "Can not save Command %s: Invalid command type "
                '"%s"' % (self.name, self.command_type)
            )

        if self.output_type not in BrewtilsCommand.OUTPUT_TYPES:
            raise BrewmasterModelValidationError(
                'Can not save Command %s: Invalid output type "%s"'
                % (self.name, self.output_type)
            )

        if len(self.parameters) != len(
            set(parameter.key for parameter in self.parameters)
        ):
            raise BrewmasterModelValidationError(
                "Can not save Command %s: Contains Parameters "
                "with duplicate keys" % self.name
            )


class Instance(Document, BrewtilsInstance):
    """Mongo-Backed BREWMASTER Instance Object"""

    name = StringField(required=True, default="default")
    description = StringField()
    status = StringField(default="INITIALIZING")
    status_info = EmbeddedDocumentField("StatusInfo", default=StatusInfo())
    queue_type = StringField()
    queue_info = DictField()
    icon_name = StringField()
    metadata = DictField()

    def __str__(self):
        return BrewtilsInstance.__str__(self)

    def __repr__(self):
        return BrewtilsInstance.__repr__(self)

    def clean(self):
        """Validate before saving to the database"""

        if self.status not in BrewtilsInstance.INSTANCE_STATUSES:
            raise BrewmasterModelValidationError(
                "Can not save Instance %s: Invalid status '%s' "
                "provided." % (self.name, self.status)
            )


class Request(Document, BrewtilsRequest):
    """Mongo-Backed BREWMASTER Request Object"""

    # These fields are duplicated for job types, changes to this field
    # necessitate a change to the RequestTemplateSchema in brewtils.
    TEMPLATE_FIELDS = {
        "system": {"field": StringField, "kwargs": {"required": True}},
        "system_version": {"field": StringField, "kwargs": {"required": True}},
        "instance_name": {"field": StringField, "kwargs": {"required": True}},
        "command": {"field": StringField, "kwargs": {"required": True}},
        "parameters": {"field": DictField, "kwargs": {}},
        "comment": {"field": StringField, "kwargs": {"required": False}},
        "metadata": {"field": DictField, "kwargs": {}},
    }

    for field_name, field_info in TEMPLATE_FIELDS.items():
        locals()[field_name] = field_info["field"](**field_info["kwargs"])

    parent = ReferenceField(
        "Request", dbref=True, required=False, reverse_delete_rule=CASCADE
    )
    children = DummyField(required=False)
    output = StringField()
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

    def __str__(self):
        return BrewtilsRequest.__str__(self)

    def __repr__(self):
        return BrewtilsRequest.__repr__(self)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.utcnow()
        super(Request, self).save(*args, **kwargs)

    def clean(self):
        """Validate before saving to the database"""

        if self.status not in BrewtilsRequest.STATUS_LIST:
            raise BrewmasterModelValidationError(
                'Can not save Request %s: Invalid status "%s"'
                % (str(self), self.status)
            )

        if (
            self.command_type is not None
            and self.command_type not in BrewtilsRequest.COMMAND_TYPES
        ):
            raise BrewmasterModelValidationError(
                "Can not save Request %s: Invalid "
                'command type "%s"' % (str(self), self.command_type)
            )

        if (
            self.output_type is not None
            and self.output_type not in BrewtilsRequest.OUTPUT_TYPES
        ):
            raise BrewmasterModelValidationError(
                "Can not save Request %s: Invalid output "
                'type "%s"' % (str(self), self.output_type)
            )

    @staticmethod
    def find_or_none(system_id):
        """Find a particular System

         :param system_id: The ID of the system to search for
         :return: The system with the given id, or None if system does not exist
         """
        try:
            return Request.objects.get(id=system_id)
        except DoesNotExist:
            return None


class System(Document, BrewtilsSystem):
    """Mongo-Backed BREWMASTER System Object"""

    name = StringField(required=True)
    description = StringField()
    version = StringField(required=True)
    max_instances = IntField(default=1)
    instances = ListField(ReferenceField(Instance, reverse_delete_rule=PULL))
    commands = ListField(ReferenceField(Command, reverse_delete_rule=PULL))
    icon_name = StringField()
    display_name = StringField()
    metadata = DictField()

    meta = {
        "auto_create_index": False,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [
            {"name": "unique_index", "fields": ["name", "version"], "unique": True}
        ],
    }

    def __str__(self):
        return BrewtilsSystem.__str__(self)

    def __repr__(self):
        return BrewtilsSystem.__repr__(self)

    def clean(self):
        """Validate before saving to the database"""

        if len(self.instances) > self.max_instances:
            raise BrewmasterModelValidationError(
                "Can not save System %s: Number of instances (%s) "
                "exceeds system limit (%s)"
                % (str(self), len(self.instances), self.max_instances)
            )

        if len(self.instances) != len(
            set(instance.name for instance in self.instances)
        ):
            raise BrewmasterModelValidationError(
                "Can not save System %s: Duplicate instance names" % str(self)
            )

    def upsert_commands(self, commands):
        """Updates or inserts a list of commands.

        Assumes the commands passed in are more important than what is currently in the db. It
        will delete commands that are not listed in the dictionary.

        :param commands: The list of new commands
        :return: None
        """
        old_commands = Command.objects(system=self)
        old_names = {command.name: command.id for command in old_commands}

        new_commands = copy.copy(commands)
        for command in new_commands:
            # If this command is already in the DB we want to preserve the ID
            if command.name in list(old_names.keys()):
                command.id = old_names[command.name]

            command.system = self
            command.save()

        # Clean up orphan commands
        new_names = [command.name for command in new_commands]
        for command in old_commands:
            if command.name not in new_names:
                command.delete()

        self.commands = new_commands
        self.save()

    def deep_save(self):
        """Deep save. Saves Commands, Instances, and the System

        Mongoengine cannot save bidirectional references in one shot because
        'You can only reference documents once they have been saved to the database'
        So we must mangle the System to have no Commands, save it, save the individual Commands
        with the System reference, update the System with the Command list, and then save the
        System again
        """

        # Note if this system is already saved
        delete_on_error = self.id is None

        # Save these off here so we can 'revert' in case of an exception
        temp_commands = self.commands
        temp_instances = self.instances

        try:
            # Before we start saving things try to make sure everything will validate correctly
            # This means multiple passes through the collections, but we want to minimize the
            # chances of having to bail out after saving something since we don't have transactions

            # However, we have to start by saving the System. We need it in the database so the
            # Commands will validate against it correctly (the ability to undo this is why we
            # saved off delete_on_error earlier) The reference lists must be empty or else we
            # encounter the bidirectional reference issue
            self.commands = []
            self.instances = []
            self.save()

            # Make sure all commands have the correct System reference
            for command in temp_commands:
                command.system = self

            # Now validate
            for command in temp_commands:
                command.validate()
            for instance in temp_instances:
                instance.validate()

            # All validated, now save everything
            for command in temp_commands:
                command.save(validate=False)
            for instance in temp_instances:
                instance.save(validate=False)
            self.commands = temp_commands
            self.instances = temp_instances
            self.save()

        # Since we don't have actual transactions we are not in a good position here, try our
        # best to 'roll back'
        except Exception:
            self.commands = temp_commands
            self.instances = temp_instances
            if delete_on_error and self.id:
                self.delete()
            raise

    def deep_delete(self):
        """Completely delete a system"""
        self.delete_commands()
        self.delete_instances()
        return self.delete()

    def delete_commands(self):
        """Delete all commands associated with this system"""
        for command in self.commands:
            command.delete()

    def delete_instances(self):
        """Delete all instances associated with this system"""
        for instance in self.instances:
            instance.delete()

    @classmethod
    def find_unique(cls, name, version):
        """Find a unique system using its name and version

        :param name: The name
        :param version: The version
        :return: One system instance if found, None otherwise
        """
        try:
            return cls.objects.get(name=name, version=version)
        except DoesNotExist:
            return None


class Event(Document, BrewtilsEvent):

    name = StringField(required=True)
    payload = DictField()
    error = BooleanField()
    metadata = DictField()
    timestamp = DateTimeField()

    def __str__(self):
        return BrewtilsEvent.__str__(self)

    def __repr__(self):
        return BrewtilsEvent.__repr__(self)


class Role(Document, BrewtilsRole):

    name = StringField(required=True)
    description = StringField()
    roles = ListField(field=ReferenceField("Role", reverse_delete_rule=PULL))
    permissions = ListField(field=StringField())

    meta = {
        "auto_create_index": False,  # We need to manage this ourselves
        "index_background": True,
        "indexes": [{"name": "unique_index", "fields": ["name"], "unique": True}],
    }


class Principal(Document, BrewtilsPrincipal):

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


class RequestTemplate(EmbeddedDocument, BrewtilsRequestTemplate):

    for field_name, field_info in Request.TEMPLATE_FIELDS.items():
        locals()[field_name] = field_info["field"](**field_info["kwargs"])

    def __str__(self):
        return BrewtilsRequestTemplate.__str__(self)

    def __repr__(self):
        return BrewtilsRequestTemplate.__repr__(self)


class DateTrigger(EmbeddedDocument, BrewtilsDateTrigger):

    run_date = DateTimeField(required=True)
    timezone = StringField(required=False, default="utc", chocies=pytz.all_timezones)

    def __str__(self):
        return BrewtilsDateTrigger.__str__(self)

    def __repr__(self):
        return BrewtilsDateTrigger.__repr__(self)

    @staticmethod
    def get_scheduler_attribute_names():
        return ["run_date", "timezone"]

    def get_scheduler_kwargs(self):
        """Get kwargs for schedulers version of this trigger."""
        tz = pytz.timezone(self.timezone)
        localized_date = tz.localize(self.run_date)
        return {"run_date": localized_date, "timezone": tz}


class IntervalTrigger(EmbeddedDocument, BrewtilsIntervalTrigger):

    weeks = IntField(default=0)
    days = IntField(default=0)
    hours = IntField(default=0)
    minutes = IntField(default=0)
    seconds = IntField(default=0)
    start_date = DateTimeField(required=False)
    end_date = DateTimeField(required=False)
    timezone = StringField(required=False, default="utc", chocies=pytz.all_timezones)
    jitter = IntField(required=False)

    def __str__(self):
        return BrewtilsIntervalTrigger.__str__(self)

    def __repr__(self):
        return BrewtilsIntervalTrigger.__repr__(self)

    @staticmethod
    def get_scheduler_attribute_names():
        return [
            "weeks",
            "days",
            "hours",
            "minutes",
            "seconds",
            "start_date",
            "end_date",
            "timezone",
            "jitter",
        ]

    def get_scheduler_kwargs(self):
        """Get kwargs for schedulers version of this trigger."""
        tz = pytz.timezone(self.timezone)
        start_date = tz.localize(self.start_date) if self.start_date else None
        end_date = tz.localize(self.start_date) if self.start_date else None
        kwargs = {"timezone": tz, "start_date": start_date, "end_date": end_date}
        for key in self.get_scheduler_attribute_names():
            if key in ["timezone", "start_date", "end_date"]:
                continue

            kwargs[key] = getattr(self, key)
        return kwargs


class CronTrigger(EmbeddedDocument, BrewtilsCronTrigger):

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

    def __str__(self):
        return BrewtilsCronTrigger.__str__(self)

    def __repr__(self):
        return BrewtilsCronTrigger.__repr__(self)

    @staticmethod
    def get_scheduler_attribute_names():
        return [
            "year",
            "month",
            "day",
            "week",
            "day_of_week",
            "hour",
            "minute",
            "second",
            "start_date",
            "end_date",
            "timezone",
            "jitter",
        ]

    def get_scheduler_kwargs(self):
        """Get kwargs for schedulers version of this trigger."""
        tz = pytz.timezone(self.timezone)
        start_date = tz.localize(self.start_date) if self.start_date else None
        end_date = tz.localize(self.start_date) if self.start_date else None
        kwargs = {"timezone": tz, "start_date": start_date, "end_date": end_date}
        for key in self.get_scheduler_attribute_names():
            if key in ["timezone", "start_date", "end_date"]:
                continue

            kwargs[key] = getattr(self, key)
        return kwargs


class Job(Document, BrewtilsJob):

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
    }

    name = StringField(required=True)
    trigger_type = StringField(required=True, choices=BrewtilsJob.TRIGGER_TYPES)
    trigger = GenericEmbeddedDocumentField(choices=list(TRIGGER_MODEL_MAPPING.values()))
    request_template = EmbeddedDocumentField("RequestTemplate")
    misfire_grace_time = IntField()
    coalesce = BooleanField(default=True)
    next_run_time = DateTimeField()
    success_count = IntField(required=True, default=0, min_value=0)
    error_count = IntField(required=True, default=0, min_value=0)
    status = StringField(
        required=True, choices=BrewtilsJob.STATUS_TYPES, default="RUNNING"
    )

    def __str__(self):
        return BrewtilsJob.__str__(self)

    def __repr__(self):
        return BrewtilsJob.__repr__(self)

    def clean(self):
        """Validate before saving to the database"""

        if self.trigger_type not in self.TRIGGER_MODEL_MAPPING:
            raise BrewmasterModelValidationError(
                "Cannot save job. No matching model for trigger type: %s"
                % self.trigger_type
            )

        if not isinstance(self.trigger, self.TRIGGER_MODEL_MAPPING[self.trigger_type]):
            raise BrewmasterModelValidationError(
                "Cannot save job. Trigger type: %s but got trigger: %s"
                % (self.trigger_type, type(self.trigger))
            )
