# -*- coding: utf-8 -*-
from copy import copy

from brewtils.schema_parser import SchemaParser

import beer_garden.db.mongo.models


class MongoParser(SchemaParser):
    """Class responsible for converting JSON into Mongo-backed objects."""

    _models = copy(SchemaParser._models)
    _models.update(
        {
            "System": beer_garden.db.mongo.models.System,
            "Instance": beer_garden.db.mongo.models.Instance,
            "Command": beer_garden.db.mongo.models.Command,
            "Connection": beer_garden.db.mongo.models.Connection,
            "Parameter": beer_garden.db.mongo.models.Parameter,
            "Request": beer_garden.db.mongo.models.Request,
            "RequestTemplate": beer_garden.db.mongo.models.RequestTemplate,
            "Choices": beer_garden.db.mongo.models.Choices,
            "Event": beer_garden.db.mongo.models.Event,
            "User": beer_garden.db.mongo.models.User,
            "Role": beer_garden.db.mongo.models.Role,
            "UpstreamRole": beer_garden.db.mongo.models.UpstreamRole,
            "Job": beer_garden.db.mongo.models.Job,
            "DateTrigger": beer_garden.db.mongo.models.DateTrigger,
            "IntervalTrigger": beer_garden.db.mongo.models.IntervalTrigger,
            "FileTrigger": beer_garden.db.mongo.models.FileTrigger,
            "CronTrigger": beer_garden.db.mongo.models.CronTrigger,
            "StatusInfo": beer_garden.db.mongo.models.StatusInfo,
            "StatusHistory": beer_garden.db.mongo.models.StatusHistory,
            "Garden": beer_garden.db.mongo.models.Garden,
            "File": beer_garden.db.mongo.models.File,
            "FileChunk": beer_garden.db.mongo.models.FileChunk,
            "UserToken": beer_garden.db.mongo.models.UserToken,
            "Topic": beer_garden.db.mongo.models.Topic,
            "Subscriber": beer_garden.db.mongo.models.Subscriber,
            "Replication": beer_garden.db.mongo.models.Replication,
            "AliasUserMap": beer_garden.db.mongo.models.AliasUserMap,
        }
    )

    @classmethod
    def _get_schema_name(cls, obj):
        if isinstance(obj, beer_garden.db.mongo.models.MongoModel):
            return obj.brewtils_model.__name__
        return super(MongoParser, cls)._get_schema_name(obj)

    @classmethod
    def _single_item(cls, obj):
        # Mongo documents are instances of Iterable, so the normal check from the
        # SchemaParser will fail unless we tweak it
        if isinstance(obj, beer_garden.db.mongo.models.MongoModel):
            return True
        return super(MongoParser, cls)._single_item(obj)
