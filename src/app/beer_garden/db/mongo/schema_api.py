import json
import logging
from typing import Optional

import pymongo
from box import Box
from gridfs.asynchronous import AsyncGridFSBucket
from pymongo import AsyncMongoClient

import beer_garden.config as config
from beer_garden.db.mongo.schema import (
    ModelItem,
    ModelType,
    from_brewtils,
    get_collection_schema,
    to_brewtils,
)

logger = logging.getLogger(__name__)
async_db: Optional[AsyncMongoClient] = None


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

async def update_one(
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
    logger.error(f"Update One :: Type = {type(collection)} == {collection} :: filter = {raw_query} :: update = {update}")
    return await async_db[collection].update_one(filter=raw_query, update=update)

async def update(update: ModelType) -> Optional[ModelItem]:
    """Update a single document

    Returns:
        None

    """

    schema = get_collection_schema(update)

    update_dict = from_brewtils(update, schema)

    updated_model = await update_one(collection=schema.collection, raw_query={"_id": update_dict["_id"]}, update={"$set": update_dict})

    return to_brewtils(updated_model, schema)


async def query(model: ModelType, **kwargs):
    schema = get_collection_schema(model)

    query = kwargs.get("raw_query", None)
    order_by = kwargs.get("order_by", None)
    include_fields = kwargs.get("include_fields", None)
    exclude_fields = kwargs.get("exclude_fields", None)
    start = int(kwargs.get("start")) if kwargs.get("start") else None
    length = int(kwargs.get("length")) if kwargs.get("length") else None

    find_kwargs = {}
    find_fields = None

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

    cursor = async_db[schema.collection].find(query, find_fields, **find_kwargs)

    docs = await cursor.to_list(length=length)

    return to_brewtils(docs, schema)


async def query_unique(model: ModelType, **kwargs):
    schema = get_collection_schema(model)

    filter = kwargs.get("raw_query", None)

    include_fields = kwargs.get("include_fields", None)
    exclude_fields = kwargs.get("exclude_fields", None)

    find_fields = kwargs.get("projection", None)

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

    logger.error(f"Unique Query {schema.collection}: Filter = {filter}, projection={find_fields}")
    doc = await async_db[schema.collection].find_one(
        filter=filter,
        projection=find_fields,
    )

    return to_brewtils(doc, schema)


async def create(obj: ModelItem) -> ModelItem:
    """Save a new item to the database

    Args:
        obj: The Brewtils model to save

    Returns:
        The saved Brewtils model

    """

    schema = get_collection_schema(obj)

    mongo_obj = await async_db[schema.collection].insert_one(from_brewtils(obj, schema))

    return to_brewtils(mongo_obj)


async def gridfs_read(filter: dict):
    fs = AsyncGridFSBucket(async_db)
    file_doc = fs.find_one(filter)

    if file_doc:
        content = await file_doc.read()
        return json.loads(content.decode("utf-8"))

    return None


async def gridfs_exists(filter: dict) -> bool:
    fs = AsyncGridFSBucket(async_db)
    file_doc = fs.find_one(filter)

    if file_doc:
        return True

    return False


async def gridfs_create(model: dict, **kwargs) -> str:
    fs = AsyncGridFSBucket(async_db)

    file_id = await fs.put(json.dumps(model), encoding="utf-8", **kwargs)

    return file_id


async def gridfs_update_metadata(filter: dict, metadata_updates: dict):

    await async_db["fs.files"].update_one(
        filter,
        {"$set": metadata_updates},
    )
    await async_db["fs.chunks"].update_many(
        filter,
        {"$set": metadata_updates},
    )


async def gridfs_delete(filter: dict):
    await async_db["fs.files"].delete_many(filter)
    await async_db["fs.chunks"].delete_many(filter)
