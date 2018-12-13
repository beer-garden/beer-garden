from copy import copy

from marshmallow import fields
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
    AppState,
)
from brewtils.errors import BrewmasterModelValidationError
from brewtils.schema_parser import SchemaParser
from brewtils.schemas import BaseSchema


class AppStateSchema(BaseSchema):
    versions = fields.Dict(allow_none=True)
    auth = fields.Dict(allow_none=True)


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
            "AppStateSchema": AppState,
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

    @classmethod
    def serialize_app_state(cls, app_state, to_string=True, **kwargs):
        return cls._do_serialize(AppStateSchema(**kwargs), app_state, to_string)

    @classmethod
    def parse_app_state(cls, app_state, from_string=False, **kwargs):
        return cls._do_parse(
            app_state, AppStateSchema(**kwargs), from_string=from_string
        )
