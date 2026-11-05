# -*- coding: utf-8 -*-
import logging
from typing import List, Optional, Type, Union

import brewtils.models
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


def combine_raw_query(raw_query: dict, new_query: dict):

    # If raw_query is none/empty, return new query
    if raw_query is None or len(raw_query) == 0:
        return new_query

    # If new query is none/empty, return raw_query
    if new_query is None or len(new_query) == 0:
        return raw_query

    # Append to AND query, else roll both up to an AND query
    if "$and" in raw_query:
        raw_query["$and"].append(new_query)
        return raw_query
    else:
        return {"$and": [raw_query, new_query]}


def is_id_key(key: str):
    return key == "id" or key.endswith(".id")


def update_key_value(key: str, value, suffix: str = None):

    if suffix:
        key = key.removesuffix(suffix)

    is_id = False
    if key == "id":
        key = "_id"
        is_id = True

    elif key.endswith(".id"):
        key = f"{key.removesuffix('.id')}._id"
        is_id = True

    if isinstance(value, dict) or isinstance(value, BaseModel):

        if hasattr(value, "id"):
            if not is_id:
                key = f"{key}._id"

        elif hasattr(value, "_id"):
            if not is_id:
                key = f"{key}._id"

    elif isinstance(value, list):
        if len(value) > 0 and (isinstance(value[0], dict)):
            if hasattr(value[0], "id"):
                if not is_id:
                    key = f"{key}._id"

            elif hasattr(value[0], "_id"):
                if not is_id:
                    key = f"{key}._id"

    value = update_value(key, value)

    return key, value


def update_value(key: str, value):

    if key.endswith("_id"):
        if isinstance(value, list):
            updated_values = []
            for key_value in value:
                updated_values.append(update_value(key, key_value))
            return updated_values
        if isinstance(value, str):
            try:
                return ObjectId(value)
            except InvalidId:
                return value
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, dict) or isinstance(value, BaseModel):
            if hasattr(value, "id"):
                return update_value(key, value.id)
            if hasattr(value, "_id"):
                return update_value(key, value._id)

    return value


def kwargs_raw_query(**kwargs):

    if not kwargs:
        return None

    query = kwargs.pop("raw_query", None)

    for key in kwargs:
        raw_field = key.replace("__", ".")

        if raw_field.endswith(".match"):
            match_query = kwargs_raw_query(**kwargs[key])
            raw_field, raw_value = update_key_value(raw_field, match_query, ".match")
            query = combine_raw_query(
                query,
                {raw_field: {"$elemMatch": match_query}},
            )
        elif raw_field.endswith(".in"):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key], ".in")

            query = combine_raw_query(
                query,
                {raw_field: {"$in": raw_value}},
            )
        elif raw_field.endswith(".not.contains"):

            raw_field, raw_value = update_key_value(
                raw_field, kwargs[key], ".not.contains"
            )

            query = combine_raw_query(
                query,
                {raw_field: {"$not": {"$in": raw_value}}},
            )
        elif raw_field.endswith(".contains"):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key], ".contains")

            query = combine_raw_query(
                query,
                {raw_field: {"$in": raw_value}},
            )

        elif raw_field.endswith(".gt"):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key], ".gt")
            query = combine_raw_query(
                query,
                {raw_field: {"$gt": raw_value}},
            )
        elif raw_field.endswith(".gte"):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key], ".gte")
            query = combine_raw_query(
                query,
                {raw_field: {"$gte": raw_value}},
            )
        elif raw_field.endswith(".lt"):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key], ".lt")
            query = combine_raw_query(
                query,
                {raw_field: {"$lt": raw_value}},
            )
        elif raw_field.endswith(".lte"):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key], ".lte")
            query = combine_raw_query(
                query,
                {raw_field: {"$lte": raw_value}},
            )
        elif raw_field.endswith(".exact"):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key], ".exact")
            query = combine_raw_query(
                query,
                {raw_field: raw_value},
            )
        elif raw_field.endswith(".not.startswith"):
            raw_field, raw_value = update_key_value(
                raw_field, kwargs[key], ".not.startswith"
            )
            query = combine_raw_query(
                query,
                {
                    raw_field.removesuffix(".exact"): {
                        "$not": {"$regex": f"^{raw_value}"}
                    }
                },
            )
        elif raw_field.endswith(".startswith"):
            raw_field, raw_value = update_key_value(
                raw_field, kwargs[key], ".startswith"
            )
            query = combine_raw_query(
                query,
                {raw_field: {"$regex": f"^{raw_value}"}},
            )

        elif raw_field.endswith(".ne"):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key], ".ne")

            query = combine_raw_query(
                query,
                {raw_field: {"$ne": raw_value}},
            )
        elif isinstance(raw_field, dict):
            query = combine_raw_query(
                query,
                {raw_field: {"$elemMatch": raw_value}},
            )
        elif isinstance(raw_field, BaseModel):
            query = combine_raw_query(
                query,
                {
                    raw_field: {
                        "$elemMatch": SchemaParser.serialize(raw_value, to_string=False)
                    }
                },
            )
        else:
            raw_field, raw_value = update_key_value(raw_field, kwargs[key])

            query = combine_raw_query(
                query,
                {raw_field: raw_value},
            )

    return query


def count(
    model_class: ModelType,
    q_filter: Union[Q, QCombination, None] = None,
    raw_query: dict = None,
    **kwargs,
) -> int:
    """Count the number of items matching a query

    Args:
        model_class: The Brewtils model class to query for
        **kwargs: Arguments to control the query. Equivalent to 'filter_params' from the
            'query' function.

    Returns:
        The number of items

    """
    # for k, v in kwargs.items():
    #     if isinstance(v, BaseModel):
    #         kwargs[k] = from_brewtils(v)

    if raw_query or kwargs:
        query_set = _model_map[model_class].objects(
            __raw__=combine_raw_query(raw_query, kwargs_raw_query(**kwargs))
        )
    else:
        query_set = _model_map[model_class].objects

    if q_filter:
        query_set = query_set.filter(q_filter)

    return query_set.count()


def query_unique(
    model_class: ModelType, raise_missing=False, raw_query: dict = None, **kwargs
) -> Optional[ModelItem]:
    """Query a collection for a unique item

    This will search a collection for a single specific item.

    If no item matching the kwarg parameters is found:
    - Will return None if raise_missing=False
    - Will raise a DoesNotExist exception if raise_missing=True

    If more than one item matching is found a MultipleObjectsReturned will be raised.

    Args:
        model_class: The Brewtils model class to query for
        raise_missing: If True, raise an exception if an item matching the query is not
            found. If False, will return None in that case.
        **kwargs: Arguments to control the query. Equivalent to 'filter_params' from the
            'query' function.

    Returns:
        A single Brewtils model

    Raises:
        mongoengine.DoesNotExist: No matching item exists (only if raise_missing=True)
        mongoengine.MultipleObjectsReturned: More than one matching item exists

    """

    try:

        include_fields = kwargs.pop("include_fields", None)
        exclude_fields = kwargs.pop("exclude_fields", None)

        if kwargs:
            raw_query = combine_raw_query(raw_query, kwargs_raw_query(**kwargs))
        if raw_query:
            query_set = _model_map[model_class].objects(__raw__=raw_query)
        else:
            query_set = _model_map[model_class].objects

        if include_fields:
            query_set = query_set.only(*include_fields)
        elif exclude_fields:
            query_set = query_set.exclude(*exclude_fields)

        return to_brewtils(query_set.get())
    except DoesNotExist:
        if raise_missing:
            raise
        return None


def query(
    model_class: ModelType, q_filter: Union[Q, QCombination, None] = None, **kwargs
) -> List[ModelItem]:
    """Query a collection

    It's possible to specify `include_fields` _and_ `exclude_fields`. This doesn't make
    a lot of sense, but you can do it. If the same field is in both `exclude_fields`
    takes priority (the field will NOT be included in the response).

    Args:
        model_class: The Brewtils model class to query for
        q_filter: Q or QCombination filter to be applied to the QuerySet
        **kwargs: Arguments to control the query. Valid options are:
            raw_query: Dict of raw mongo query
            filter_params: Dict of filtering parameters
            order_by: Field that will be used to order the result list
            include_fields: Model fields to include
            exclude_fields: Model fields to exclude
            dereference_nested: Flag specifying if related models should be fetched
            text_search: A text search parameter
            hint: A hint specifying the index to use (cannot be used with text_search)
            start: Slicing start
            length: Slicing count

    Returns:
        A list of Brewtils models

    """

    filter_params = kwargs.get("filter_params")
    raw_query = kwargs.get("raw_query")
    if filter_params:
        raw_query = combine_raw_query(raw_query, kwargs_raw_query(**filter_params))
    if raw_query:
        query_set = _model_map[model_class].objects(__raw__=raw_query)
    else:
        query_set = _model_map[model_class].objects

    if q_filter:
        query_set = query_set.filter(q_filter)

    # Bad things happen if you try to use a hint with a text search.
    if kwargs.get("text_search"):
        query_set = query_set.search_text(kwargs.get("text_search"))
    elif kwargs.get("hint"):
        # Sanity check - if index is 'bad' just let mongo deal with it
        if kwargs.get("hint") in _model_map[model_class].index_names():
            query_set = query_set.hint(kwargs.get("hint"))

    if kwargs.get("order_by"):
        query_set = query_set.order_by(kwargs.get("order_by"))

    if kwargs.get("include_fields"):
        query_set = query_set.only(*kwargs.get("include_fields"))

    if kwargs.get("exclude_fields"):
        query_set = query_set.exclude(*kwargs.get("exclude_fields"))

    if not kwargs.get("dereference_nested", True):
        query_set = query_set.no_dereference()

    if kwargs.get("start"):
        query_set = query_set.skip(int(kwargs.get("start")))

    if kwargs.get("length"):
        query_set = query_set.limit(int(kwargs.get("length")))

    return [] if len(query_set) == 0 else to_brewtils(query_set)


def create_direct(obj: ModelItem) -> ModelItem:
    """Save a new item to the database, that already has an ID

    If the Mongo model corresponding to the Brewtils model has a "pre_save"
    or "post_save" functions, those will be executed. The Original model is
    returned without any of the database modifications and is written directly
    into the collection bypassing MongoEngine

    This is not to be utilized for models that have DBRef objects

    Args:
        obj: The Brewtils model to save

    Returns:
        The provided Brewtils model

    """

    if not hasattr(obj, "id"):
        return create(obj)

    mongo_obj: MongoModel = from_brewtils(obj)
    if hasattr(mongo_obj, "_pre_save"):
        mongo_obj._pre_save()

    type(mongo_obj)._get_collection().bulk_write(
        [InsertOne(mongo_obj.to_mongo().to_dict())]
    )

    if hasattr(mongo_obj, "_post_save"):
        mongo_obj._post_save()

    return obj


def update_direct(obj: ModelItem) -> ModelItem:
    """Update a item to the database

    If the Mongo model corresponding to the Brewtils model has a "pre_save"
    or "post_save" functions, those will be executed. The Original model is
    returned without any of the database modifications and is written directly
    into the collection bypassing MongoEngine

    This is not to be utilized for models that have DBRef objects

    Args:
        obj: The Brewtils model to updated

    Returns:
        The provided Brewtils model

    """

    mongo_obj: MongoModel = from_brewtils(obj)

    mongo_obj.clean_update()

    if hasattr(mongo_obj, "_pre_save"):
        mongo_obj._pre_save()

    type(mongo_obj)._get_collection().bulk_write(
        [ReplaceOne({"_id": mongo_obj.id}, mongo_obj.to_mongo().to_dict(), upsert=True)]
    )

    if hasattr(mongo_obj, "_post_save"):
        mongo_obj._post_save()

    return obj


def create(obj: ModelItem) -> ModelItem:
    """Save a new item to the database

    If the Mongo model corresponding to the Brewtils model has a "deep_save" method
    then that will be called. Otherwise the normal "save" will be used.

    Args:
        obj: The Brewtils model to save

    Returns:
        The saved Brewtils model

    """

    mongo_obj: MongoModel = from_brewtils(obj)

    try:
        if hasattr(mongo_obj, "deep_save"):
            mongo_obj.deep_save()
        else:
            mongo_obj.save(force_insert=True)
    except NotUniqueError as ex:
        raise NotUniqueException from ex

    return to_brewtils(mongo_obj)


def update(obj: ModelItem) -> ModelItem:
    """Save changes to an item to the database

    This is almost identical to the "create" function but it also calls an additional
    clean method (clean_update) to ensure that the update is valid.

    Args:
        obj: The Brewtils model to save

    Returns:
        The saved Brewtils model

    """

    mongo_obj = from_brewtils(obj)

    mongo_obj.clean_update()

    if hasattr(mongo_obj, "deep_save"):
        mongo_obj.deep_save()
    else:
        mongo_obj.save()

    return to_brewtils(mongo_obj)


def bulk_update(objs: List[ModelItem]) -> None:
    """List of objects to bulk update. These do not invoke custom functions
        like save or update in mongoengine models

    Args:
        objs (list[ModelItem]): List of objects to bulk update
    """
    bulk_operations = {}

    for obj in objs:
        mongo_obj = from_brewtils(obj)
        mongo_obj.clean_update()
        mongo_class = type(mongo_obj)

        if mongo_class not in bulk_operations:
            bulk_operations[mongo_class] = []

        if hasattr(mongo_obj, "id") and mongo_obj.id is not None:
            bulk_operations[mongo_class].append(
                UpdateOne(
                    {"_id": mongo_obj.id}, {"$set": mongo_obj.to_mongo().to_dict()}
                )
            )
        else:
            bulk_operations[mongo_class].append(
                InsertOne(mongo_obj.to_mongo().to_dict())
            )

    if bulk_operations:
        for bulk_op in bulk_operations:
            bulk_op._get_collection().bulk_write(
                bulk_operations[bulk_op], ordered=False
            )


def modify(obj: ModelItem, query=None, **kwargs) -> ModelItem:
    """Modify an item in the database

    Args:
        obj: The Brewtils model to modify
        query: query argument, passed to Model.modify
        kwargs: Modification parameters

    Returns:
        The modified Brewtils model

    """

    mongo_obj = from_brewtils(obj)

    # If any values are brewtils models those need to be converted
    for key in kwargs:
        if isinstance(kwargs[key], BaseModel):
            kwargs[key] = from_brewtils(kwargs[key])

    # TODO: Convert this to RAW
    mongo_obj.modify(query=query, **kwargs)

    return to_brewtils(mongo_obj)


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
