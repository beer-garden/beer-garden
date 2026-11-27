# -*- coding: utf-8 -*-
import json
import logging
from typing import List, Optional, Type, Union

import brewtils.models
import gridfs
from box import Box
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser
from bson.errors import InvalidId
from bson.objectid import ObjectId
from mongoengine import (
    ConnectionFailure,
    DoesNotExist,
    NotUniqueError,
    QuerySet,
    connect,
    register_connection,
)
from mongoengine.connection import get_db
from mongoengine.queryset.visitor import Q, QCombination
from pymongo import InsertOne, ReplaceOne, UpdateOne

import beer_garden.db.mongo.models
from beer_garden.db.mongo.indexes import check_indexes, update_ttl_indexes
from beer_garden.db.mongo.migration import ensure_model_migration
from beer_garden.db.mongo.models import MongoModel
from beer_garden.db.mongo.parser import MongoParser
from beer_garden.db.mongo.util import (
    ensure_local_garden,
    is_legacy_mongodb,
    reset_last_configuration,
)
from beer_garden.errors import NotUniqueException

logger = logging.getLogger(__name__)

ModelType = Union[
    Type[brewtils.models.Command],
    Type[brewtils.models.Instance],
    Type[brewtils.models.Job],
    Type[brewtils.models.Request],
    Type[brewtils.models.RequestTemplate],
    Type[brewtils.models.System],
    Type[brewtils.models.Garden],
    Type[brewtils.models.File],
    Type[brewtils.models.FileChunk],
    Type[brewtils.models.Topic],
    Type[brewtils.models.Subscriber],
]

ModelItem = Union[
    brewtils.models.Command,
    brewtils.models.Instance,
    brewtils.models.Job,
    brewtils.models.Request,
    brewtils.models.RequestTemplate,
    brewtils.models.System,
    brewtils.models.Garden,
    brewtils.models.File,
    brewtils.models.FileChunk,
    brewtils.models.Topic,
    brewtils.models.Subscriber,
    brewtils.models.AliasUserMap,
]

_model_map = {}
for model_name in beer_garden.db.mongo.models.__all__:
    mongo_class = getattr(beer_garden.db.mongo.models, model_name)

    brewtils_model = getattr(mongo_class, "brewtils_model", None)

    if brewtils_model:
        _model_map[brewtils_model] = mongo_class


def from_brewtils(obj: ModelItem) -> MongoModel:
    """Convert an item from its Brewtils model to its Mongo one.

    Args:
        obj: The Brewtils model item

    Returns:
        The Mongo model item

    """
    model_dict = SchemaParser.serialize(obj, to_string=False)
    mongo_obj = MongoParser.parse(model_dict, type(obj), from_string=False)
    return mongo_obj


def to_brewtils(
    obj: Union[MongoModel, List[MongoModel], QuerySet],
) -> Union[ModelItem, List[ModelItem], None]:
    """Convert an item from its Mongo model to its Brewtils one

    Args:
        obj: The Mongo model item or QuerySet

    Returns:
        The Brewtils model item

    """
    if obj is None:
        return obj

    if isinstance(obj, (list, QuerySet)):
        if len(obj) == 0:
            return []

        model_class = obj[0].brewtils_model
        many = True
    else:
        model_class = obj.brewtils_model
        many = False

    if many:
        for item in obj:
            if getattr(item, "pre_serialize", None):
                item.pre_serialize()
    else:
        if getattr(obj, "pre_serialize", None):
            obj.pre_serialize()

    serialized = MongoParser.serialize(obj, to_string=True)
    parsed = SchemaParser.parse(serialized, model_class, from_string=True, many=many)

    return parsed


def check_connection(db_config: Box):
    """Check connectivity to the mongo database

    Args:
        db_config: Yapconf-generated configuration object

    Returns:
        bool: True if successful, False otherwise (unable to connect)

    Raises:
        Any mongoengine error *except* ConnectionFailure
    """
    try:
        # Set timeouts here to a low value - we don't want to wait 30
        # seconds if there's no database
        conn = connect(
            alias="aliveness",
            db=db_config["name"],
            socketTimeoutMS=1000,
            serverSelectionTimeoutMS=1000,
            **db_config["connection"],
        )

    except ConnectionFailure as ex:
        logger.debug(ex)
        return False

    try:
        # Checking for timeout error
        logger.debug("Attempting connection")
        conn.server_info()
    except Exception as ex:
        logger.debug(ex)
        return False

    return True


def create_connection(connection_alias: str = "default", db_config: Box = None) -> None:
    """Register a database connection

    Args:
        connection_alias: Alias for this connection
        db_config: Yapconf-generated configuration object

    Returns:
        None
    """
    # Now register the default connection with real timeouts
    # Yes, mongoengine uses 'db' in connect and 'name' in register_connection
    register_connection(
        connection_alias,
        name=db_config["name"],
        **db_config["connection"],
    )


def initial_setup():
    """Do everything necessary to ensure the database is in a 'good' state"""

    ensure_model_migration()

    for doc in (
        beer_garden.db.mongo.models.Garden,
        beer_garden.db.mongo.models.Job,
        beer_garden.db.mongo.models.Request,
        beer_garden.db.mongo.models.System,
        beer_garden.db.mongo.models.UserToken,
        beer_garden.db.mongo.models.User,
        beer_garden.db.mongo.models.Role,
        beer_garden.db.mongo.models.Replication,
        beer_garden.db.mongo.models.Topic,
    ):
        check_indexes(doc)

    if not is_legacy_mongodb():
        update_ttl_indexes()

    # This sets the last configuration for future migrations to reference
    reset_last_configuration()

    ensure_local_garden()


def get_job_store():
    from beer_garden.db.mongo.jobstore import MongoJobStore

    return MongoJobStore()





def delete(obj: ModelItem, force_delete: bool = False) -> None:
    """Delete an item from the database

    If the Mongo model corresponding to the Brewtils model has a "deep_delete" method
    then that will be called. Otherwise the normal "delete" will be used.

    Args:
        obj: The Brewtils model to delete

    Returns:
        None

    """
    mongo_obj = from_brewtils(obj)
    if force_delete and hasattr(mongo_obj, "force_delete"):
        mongo_obj.force_delete()
    elif hasattr(mongo_obj, "deep_delete"):
        mongo_obj.deep_delete()
    else:
        mongo_obj.delete()


def reload(obj: ModelItem) -> ModelItem:
    """Reload an item from the database

    Args:
        obj: The Brewtils model to reload

    Returns:
        The updated Brewtils model

    """
    existing_obj = _model_map[type(obj)].objects.get(id=obj.id)

    return to_brewtils(existing_obj)


def distinct(brewtils_clazz: ModelItem, field: str) -> List:
    return _model_map[brewtils_clazz].objects.distinct(field)


