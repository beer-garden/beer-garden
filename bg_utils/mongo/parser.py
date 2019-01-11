from copy import copy

from marshmallow.exceptions import MarshmallowError

from bg_utils.mongo.models import (
    System,
    Instance,
    Command,
    Parameter,
    Request,
    Choices,
    Event,
    Principal,
    Role,
    RefreshToken,
    Job,
    RequestTemplate,
    DateTrigger,
    IntervalTrigger,
    CronTrigger,
)
from brewtils.errors import BrewmasterModelValidationError
from brewtils.schema_parser import SchemaParser


class MongoParser(SchemaParser):
    """Class responsible for converting JSON into Mongo-backed objects."""

    _models = copy(SchemaParser._models)
    _models.update(
        {
            "SystemSchema": System,
            "InstanceSchema": Instance,
            "CommandSchema": Command,
            "ParameterSchema": Parameter,
            "RequestSchema": Request,
            "RequestTemplateSchema": RequestTemplate,
            "ChoicesSchema": Choices,
            "EventSchema": Event,
            "PrincipalSchema": Principal,
            "RoleSchema": Role,
            "RefreshTokenSchema": RefreshToken,
            "JobSchema": Job,
            "DateTriggerSchema": DateTrigger,
            "IntervalTriggerSchema": IntervalTrigger,
            "CronTriggerSchema": CronTrigger,
        }
    )

    @classmethod
    def _do_parse(cls, data, schema, from_string=False):
        try:
            return super(MongoParser, cls)._do_parse(
                data, schema, from_string=from_string
            )
        except (TypeError, ValueError, MarshmallowError) as ex:
            raise BrewmasterModelValidationError(str(ex))
