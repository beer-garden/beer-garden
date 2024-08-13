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
            "ConnectionSchema": beer_garden.db.mongo.models.Connection,
            "ParameterSchema": beer_garden.db.mongo.models.Parameter,
            "RequestSchema": beer_garden.db.mongo.models.Request,
            "RequestTemplateSchema": beer_garden.db.mongo.models.RequestTemplate,
            "ChoicesSchema": beer_garden.db.mongo.models.Choices,
            "EventSchema": beer_garden.db.mongo.models.Event,
            "UserSchema": beer_garden.db.mongo.models.User,
            "RoleSchema": beer_garden.db.mongo.models.Role,
            "UpstreamRoleSchema": beer_garden.db.mongo.models.UpstreamRole,
            "JobSchema": beer_garden.db.mongo.models.Job,
            "DateTriggerSchema": beer_garden.db.mongo.models.DateTrigger,
            "IntervalTriggerSchema": beer_garden.db.mongo.models.IntervalTrigger,
            "FileTriggerSchema": beer_garden.db.mongo.models.FileTrigger,
            "CronTriggerSchema": beer_garden.db.mongo.models.CronTrigger,
            "StatusInfoSchema": beer_garden.db.mongo.models.StatusInfo,
            "StatusHistorySchema": beer_garden.db.mongo.models.StatusHistory,
            "GardenSchema": beer_garden.db.mongo.models.Garden,
            "FileSchema": beer_garden.db.mongo.models.File,
            "FileChunkSchema": beer_garden.db.mongo.models.FileChunk,
            "UserTokenSchema": beer_garden.db.mongo.models.UserToken,
            "TopicSchema": beer_garden.db.mongo.models.Topic,
            "SubscriberSchema": beer_garden.db.mongo.models.Subscriber,
            "ReplicationSchema": beer_garden.db.mongo.models.Replication,
            "AliasUserMapSchema": beer_garden.db.mongo.models.AliasUserMap,
        }
    )

    @classmethod
    def _get_schema_name(cls, obj):
        if isinstance(obj, beer_garden.db.mongo.models.MongoModel):
            return obj.brewtils_model.schema
        return super(MongoParser, cls)._get_schema_name(obj)

    @classmethod
    def _single_item(cls, obj):
        # Mongo documents are instances of Iterable, so the normal check from the
        # SchemaParser will fail unless we tweak it
        if isinstance(obj, beer_garden.db.mongo.models.MongoModel):
            return True
        return super(MongoParser, cls)._single_item(obj)
