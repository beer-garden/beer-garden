from copy import copy

from marshmallow.exceptions import MarshmallowError

from bg_utils.models import System, Instance, Command, Parameter, Request, Choices, Event, Job, \
    RequestTemplate
from brewtils.errors import BrewmasterModelValidationError
from brewtils.schema_parser import SchemaParser


class BeerGardenSchemaParser(SchemaParser):
    """Class responsible for converting JSON into Mongo-backed objects."""

    _models = copy(SchemaParser._models)
    _models.update({
        'SystemSchema': System,
        'InstanceSchema': Instance,
        'CommandSchema': Command,
        'ParameterSchema': Parameter,
        'RequestSchema': Request,
        'RequestTemplateSchema': RequestTemplate,
        'ChoicesSchema': Choices,
        'EventSchema': Event,
        'JobSchema': Job,
    })

    @classmethod
    def _do_parse(cls, data, schema, from_string=False):
        try:
            return super(BeerGardenSchemaParser, cls)._do_parse(data, schema,
                                                                from_string=from_string)
        except (TypeError, ValueError, MarshmallowError) as ex:
            raise BrewmasterModelValidationError(str(ex))
