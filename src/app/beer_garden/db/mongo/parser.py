# -*- coding: utf-8 -*-
from copy import copy

from brewtils.schema_parser import SchemaParser

import beer_garden.db.mongo.models


class MongoParser(SchemaParser):
    """Class responsible for converting JSON into Mongo-backed objects."""

    _models = copy(SchemaParser._models)
    _models.update(
        {
            "SystemSchema": beer_garden.db.mongo.models.System,
            "InstanceSchema": beer_garden.db.mongo.models.Instance,
            "CommandSchema": beer_garden.db.mongo.models.Command,
            "ParameterSchema": beer_garden.db.mongo.models.Parameter,
            "RequestSchema": beer_garden.db.mongo.models.Request,
            "RequestTemplateSchema": beer_garden.db.mongo.models.RequestTemplate,
            "ChoicesSchema": beer_garden.db.mongo.models.Choices,
            "EventSchema": beer_garden.db.mongo.models.Event,
            "PrincipalSchema": beer_garden.db.mongo.models.Principal,
            "RoleSchema": beer_garden.db.mongo.models.Role,
            "RefreshTokenSchema": beer_garden.db.mongo.models.RefreshToken,
            "JobSchema": beer_garden.db.mongo.models.Job,
            "DateTriggerSchema": beer_garden.db.mongo.models.DateTrigger,
            "IntervalTriggerSchema": beer_garden.db.mongo.models.IntervalTrigger,
            "CronTriggerSchema": beer_garden.db.mongo.models.CronTrigger,
        }
    )

    @staticmethod
    def _get_schema_name(model):
        if isinstance(model, beer_garden.db.mongo.models.MongoModel):
            return model.brewtils_model.schema
