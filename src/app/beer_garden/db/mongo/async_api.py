import json
import logging
from typing import List, Optional

import pymongo
from box import Box
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser
from bson.errors import InvalidId
from bson.objectid import ObjectId
from gridfs.asynchronous import AsyncGridFSBucket
from gridfs.synchronous import GridFSBucket
from pymongo import AsyncMongoClient, InsertOne, MongoClient, ReplaceOne, UpdateOne
from pymongo.errors import DuplicateKeyError

import beer_garden.config as config
from beer_garden.db.mongo.schema import (
    ModelItem,
    ModelType,
    from_brewtils,
    get_collection_schema,
    to_brewtils,
)
from beer_garden.errors import NotFoundException, NotUniqueException

logger = logging.getLogger(__name__)
async_db: Optional[AsyncMongoClient] = None
sync_db: Optional[MongoClient] = None


def async_create_connection(db_config: Box = None) -> None:
    """Register a database connection

    Args:
        db_config: Yapconf-generated configuration object

    Returns:
        None
    """
    global async_db

    async_conn = AsyncMongoClient(
        host=config.get("connection.host", db_config),
        port=config.get("connection.port", db_config),
        username=config.get("connection.username", db_config),
        password=config.get("connection.password", db_config),
        authSource=config.get("connection.authentication_source", db_config),
        tz_aware=True,
    )
    async_db = async_conn[config.get("name", db_config)]


def create_connection(db_config: Box = None) -> None:
    """Register a database connection

    Args:
        db_config: Yapconf-generated configuration object

    Returns:
        None
    """
    global sync_db

    sync_conn = MongoClient(
        host=config.get("connection.host", db_config),
        port=config.get("connection.port", db_config),
        username=config.get("connection.username", db_config),
        password=config.get("connection.password", db_config),
        authSource=config.get("connection.authentication_source", db_config),
        tz_aware=True,
    )
    sync_db = sync_conn[config.get("name", db_config)]


def check_connection():
    pass


def get_job_store():
    pass


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

    if isinstance(value, BaseModel):
        value = SchemaParser.serialize(value, to_string=False)

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

    if key == "_id" or key.endswith("__id") or key.endswith("._id"):
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
            if isinstance(kwargs[key], dict) or isinstance(kwargs[key], BaseModel):
                match_query = kwargs_raw_query(**kwargs[key])
                raw_field, raw_value = update_key_value(
                    raw_field, match_query, ".match"
                )
                query = combine_raw_query(
                    query,
                    {raw_field: {"$elemMatch": raw_value}},
                )
            else:
                raw_field, raw_value = update_key_value(raw_field, kwargs[key])
                query = combine_raw_query(
                    query,
                    {raw_field: raw_value},
                )
        elif raw_field.endswith(".nin"):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key], ".nin")

            query = combine_raw_query(
                query,
                {raw_field: {"$not": {"$in": raw_value}}},
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
        elif isinstance(raw_field, dict) or isinstance(raw_field, BaseModel):
            raw_field, raw_value = update_key_value(raw_field, kwargs[key])
            query = combine_raw_query(
                query,
                {raw_field: {"$elemMatch": raw_value}},
            )
        else:
            raw_field, raw_value = update_key_value(raw_field, kwargs[key])

            query = combine_raw_query(
                query,
                {raw_field: raw_value},
            )

    return query


def _query_variables(model_class: ModelType, **kwargs):

    schema = get_collection_schema(model_class)

    raw_query = kwargs.pop("raw_query", None)
    filter_params = kwargs.pop("filter_params", None)

    include_fields = kwargs.pop("include_fields", None)
    exclude_fields = kwargs.pop("exclude_fields", None)

    find_fields = kwargs.pop("projection", None)
    order_by = kwargs.pop("order_by", None)
    start = int(kwargs.pop("start")) if kwargs.get("start") else None
    length = int(kwargs.pop("length")) if kwargs.get("length") else None

    text_search = kwargs.pop("text_search", None)

    hint = kwargs.pop("hint", None)

    filter = combine_raw_query(raw_query, kwargs_raw_query(**kwargs))
    if filter_params:
        filter = combine_raw_query(filter, kwargs_raw_query(**filter_params))

    if text_search:
        filter = combine_raw_query(filter, {"$text": {"$search": text_search}})

    find_kwargs = {}

    if include_fields:
        if find_fields is None:
            find_fields = {}

        for include_field in include_fields:
            find_fields[include_field] = 1
    if exclude_fields:
        if find_fields is None:
            find_fields = {}

        for exclude_field in exclude_fields:
            find_fields[exclude_field] = 0

    if order_by:
        if order_by.startswith("-"):
            find_kwargs["sort"] = [(order_by[1:], pymongo.DESCENDING)]
        else:
            find_kwargs["sort"] = [(order_by, pymongo.ASCENDING)]

    if start is not None:
        find_kwargs["skip"] = start

    if length is not None:
        find_kwargs["limit"] = length

    if (
        hint
        and len(schema.indexes) > 0
        and any(index["name"] == hint for index in schema.indexes)
    ):
        find_kwargs["hint"] = hint

    return (schema, filter, find_fields, find_kwargs, length)


async def async_count(
    model_class: ModelType,
    **kwargs,
) -> int:
    """Count the number of items matching a query

    Args:
        model_class: The Brewtils model class to query for
        raw_query:
        **kwargs: Arguments to control the query. Equivalent to 'filter_params' from the
            'query' function.

    Returns:
        The number of items

    """

    schema, filter, *_ = _query_variables(model_class, **kwargs)

    total = await async_db[schema.collection].count_documents(filter)

    return total


def count(
    model_class: ModelType,
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
    schema, filter, *_ = _query_variables(model_class, **kwargs)

    total = sync_db[schema.collection].count_documents(filter)

    return total


async def async_update_one(
    collection: str | ModelType = None, raw_query: dict = None, update: dict = None
) -> None:
    """Update a single document

    Args:
        collection: Name of collection to modify
        filter: Filter parameters
        update: Update parameter

    Returns:
        None

    """

    if not isinstance(collection, str):
        schema = get_collection_schema(collection)
        collection = schema.collection
    return await async_db[collection].update_one(filter=raw_query, update=update)


def update_one(
    collection: str | ModelType = None, raw_query: dict = None, update: dict = None
) -> None:
    """Update a single document

    Args:
        collection: Name of collection to modify
        filter: Filter parameters
        update: Update parameter

    Returns:
        None

    """

    if not isinstance(collection, str):
        schema = get_collection_schema(collection)
        collection = schema.collection
    return sync_db[collection].update_one(filter=raw_query, update=update)


async def async_update(update: ModelType) -> Optional[ModelItem]:
    """Update a single document

    Returns:
        None

    """

    schema = get_collection_schema(update)

    update_dict = from_brewtils(update, schema)

    updated_model = await update_one(
        collection=schema.collection,
        raw_query={"_id": update_dict["_id"]},
        update={"$set": update_dict},
    )

    return to_brewtils(updated_model, schema)


def update(update: ModelType) -> Optional[ModelItem]:
    """Update a single document

    Returns:
        None

    """

    schema = get_collection_schema(update)

    update_dict = from_brewtils(update, schema)

    updated_model = update_one(
        collection=schema.collection,
        raw_query={"_id": update_dict["_id"]},
        update={"$set": update_dict},
    )

    return to_brewtils(updated_model, schema)


async def async_query(model: ModelType, **kwargs):

    schema, filter, find_fields, find_kwargs, length = _query_variables(model, **kwargs)
    cursor = async_db[schema.collection].find(filter, find_fields, **find_kwargs)

    docs = await cursor.to_list(length=length)

    return to_brewtils(docs, schema)


def query(model: ModelType, **kwargs):
    schema, filter, find_fields, find_kwargs, length = _query_variables(model, **kwargs)

    cursor = sync_db[schema.collection].find(filter, find_fields, **find_kwargs)

    docs = cursor.to_list(length=length)

    return to_brewtils(docs, schema)


async def async_query_unique(model: ModelType, raise_missing=False, **kwargs):
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
        NotFoundException: No matching item exists (only if raise_missing=True)

    """
    schema, filter, find_fields, *_ = _query_variables(model, **kwargs)
    doc = await async_db[schema.collection].find_one(
        filter=filter,
        projection=find_fields,
    )

    if doc is None and raise_missing:
        raise NotFoundException

    return to_brewtils(doc, schema)


def query_unique(model: ModelType, raise_missing=False, **kwargs):
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
        NotFoundException: No matching item exists (only if raise_missing=True)
    """
    schema, filter, find_fields, *_ = _query_variables(model, **kwargs)
    doc = sync_db[schema.collection].find_one(
        filter=filter,
        projection=find_fields,
    )

    if doc is None and raise_missing:
        raise NotFoundException

    return to_brewtils(doc, schema)


async def async_create(obj: ModelItem) -> ModelItem:
    """Save a new item to the database

    Args:
        obj: The Brewtils model to save

    Returns:
        The saved Brewtils model

    """

    schema = get_collection_schema(obj)

    try:
        mongo_obj = await async_db[schema.collection].insert_one(
            from_brewtils(obj, schema)
        )

        return to_brewtils(mongo_obj)
    except DuplicateKeyError as ex:
        raise NotUniqueException from ex


def create(obj: ModelItem) -> ModelItem:
    """Save a new item to the database

    Args:
        obj: The Brewtils model to save

    Returns:
        The saved Brewtils model

    """

    schema = get_collection_schema(obj)

    try:
        mongo_obj = sync_db[schema.collection].insert_one(from_brewtils(obj, schema))

        return to_brewtils(mongo_obj)
    except DuplicateKeyError as ex:
        raise NotUniqueException from ex


def _modify_updates(**kwargs):
    push_values = {}
    pull_values = {}
    inc_values = {}
    set_values = {}
    for key in kwargs:
        if isinstance(kwargs[key], BaseModel):
            kwargs[key] = from_brewtils(kwargs[key])
        new_key = key.replace("__", ".").replace(".S.", ".$[].")

        if new_key.startswith("inc."):
            new_key = new_key.replace("inc.", 1)
            inc_values[new_key] = kwargs[key]
        elif new_key.startswith("pull."):
            new_key = new_key.replace("pull.", 1)
            pull_values[new_key] = kwargs[key]
        elif new_key.startswith("push.all."):
            new_key = new_key.replace("push.all.", 1)
            push_values[new_key] = {"$each": kwargs[key]}
        elif new_key.startswith("set."):
            new_key = new_key.replace("set.", 1)
            set_values[new_key] = kwargs[key]
        else:
            set_values[new_key] = kwargs[key]

    return {
        "$set": set_values,
        "$push": push_values,
        "$inc": inc_values,
        "$pull": pull_values,
    }


async def async_modify(obj: ModelItem, query=None, **kwargs) -> ModelItem:
    """Modify an item in the database

    Args:
        obj: The Brewtils model to modify
        query: query argument, passed to Model.modify
        kwargs: Modification parameters

    Returns:
        The modified Brewtils model

    """

    schema = get_collection_schema(obj)

    # If any values are brewtils models those need to be converted
    updates = _modify_updates(**kwargs)

    if query is None:
        source_dict = from_brewtils(obj, schema)
        updated_model = await async_update_one(
            collection=schema.collection,
            raw_query={"_id": source_dict["_id"]},
            update=updates,
        )
    else:
        filter = kwargs_raw_query(**query)
        updated_model = await async_update_one(
            collection=schema.collection,
            raw_query=filter,
            update=updates,
        )

    return to_brewtils(updated_model, schema)


def modify(obj: ModelItem, query=None, **kwargs) -> ModelItem:
    """Modify an item in the database

    Args:
        obj: The Brewtils model to modify
        query: query argument, passed to Model.modify
        kwargs: Modification parameters

    Returns:
        The modified Brewtils model

    """

    schema = get_collection_schema(obj)

    # If any values are brewtils models those need to be converted
    updates = _modify_updates(**kwargs)

    if query is None:
        source_dict = from_brewtils(obj, schema)
        updated_model = update_one(
            collection=schema.collection,
            raw_query={"_id": source_dict["_id"]},
            update=updates,
        )
    else:
        filter = kwargs_raw_query(**query)
        updated_model = update_one(
            collection=schema.collection,
            raw_query=filter,
            update=updates,
        )

    return to_brewtils(updated_model, schema)


def _bulk_operations(objs: List[ModelItem]):
    bulk_operations = {}

    for obj in objs:
        schema = get_collection_schema(update)

        mongo_obj = from_brewtils(obj, schema)

        if schema.collection not in bulk_operations:
            bulk_operations[schema.collection] = []

        if "_id" in mongo_obj and mongo_obj["_id"] is not None:
            bulk_operations[schema.collection].append(
                UpdateOne({"_id": mongo_obj["_id"]}, {"$set": mongo_obj})
            )
        else:
            bulk_operations[schema.collection].append(InsertOne(mongo_obj))

    return bulk_operations


async def async_bulk_update(objs: List[ModelItem]) -> None:
    """List of objects to bulk update. These do not invoke custom functions
        like save or update in mongoengine models

    Args:
        objs (list[ModelItem]): List of objects to bulk update
    """
    bulk_operations = _bulk_operations(objs)

    if bulk_operations:
        for bulk_op in bulk_operations:
            await async_db[bulk_op].bulk_write(bulk_operations[bulk_op], ordered=False)


def bulk_update(objs: List[ModelItem]) -> None:
    """List of objects to bulk update. These do not invoke custom functions
        like save or update in mongoengine models

    Args:
        objs (list[ModelItem]): List of objects to bulk update
    """
    bulk_operations = _bulk_operations(objs)

    if bulk_operations:
        for bulk_op in bulk_operations:
            sync_db[bulk_op].bulk_write(bulk_operations[bulk_op], ordered=False)


async def async_gridfs_read(filter: dict):
    fs = AsyncGridFSBucket(async_db)
    file_doc = fs.find_one(filter)

    if file_doc:
        content = await file_doc.read()
        return json.loads(content.decode("utf-8"))

    return None


def gridfs_read(filter: dict):
    fs = GridFSBucket(sync_db)
    file_doc = fs.find_one(filter)

    if file_doc:
        content = file_doc.read()
        return json.loads(content.decode("utf-8"))

    return None


async def async_gridfs_exists(filter: dict) -> bool:
    fs = AsyncGridFSBucket(async_db)
    file_doc = fs.find_one(filter)

    if file_doc:
        return True

    return False


def gridfs_exists(filter: dict) -> bool:
    fs = GridFSBucket(sync_db)
    file_doc = fs.find_one(filter)

    if file_doc:
        return True

    return False


async def async_gridfs_create(model: dict, **kwargs) -> str:
    fs = AsyncGridFSBucket(async_db)

    file_id = await fs.put(json.dumps(model), encoding="utf-8", **kwargs)

    return file_id


def gridfs_create(model: dict, **kwargs) -> str:
    fs = GridFSBucket(sync_db)

    file_id = fs.put(json.dumps(model), encoding="utf-8", **kwargs)

    return file_id


async def async_gridfs_update_metadata(filter: dict, metadata_updates: dict):

    await async_db["fs.files"].update_one(
        filter,
        {"$set": metadata_updates},
    )
    await async_db["fs.chunks"].update_many(
        filter,
        {"$set": metadata_updates},
    )


def gridfs_update_metadata(filter: dict, metadata_updates: dict):

    sync_db["fs.files"].update_one(
        filter,
        {"$set": metadata_updates},
    )
    sync_db["fs.chunks"].update_many(
        filter,
        {"$set": metadata_updates},
    )


async def async_gridfs_delete(filter: dict):
    await async_db["fs.files"].delete_many(filter)
    await async_db["fs.chunks"].delete_many(filter)


def gridfs_delete(filter: dict):
    sync_db["fs.files"].delete_many(filter)
    sync_db["fs.chunks"].delete_many(filter)
