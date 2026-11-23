import json
import logging
from typing import Optional, Type, Union

import brewtils.models
import pymongo
from box import Box
from brewtils.schema_parser import SchemaParser
from bson import ObjectId
from gridfs.asynchronous import AsyncGridFSBucket
from pymongo import AsyncMongoClient

import beer_garden.config as config
from beer_garden.db.mongo.schema import MongoSchema, get_collection_schema

logger = logging.getLogger(__name__)
async_db: Optional[AsyncMongoClient] = None

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
]


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


def clean_id(doc, to_mongo=False):
    if to_mongo:
        if "id" in doc:
            doc["_id"] = ObjectId(doc["id"])
            del doc["id"]
    else:
        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]

    return doc


def to_brewtils(doc: dict | list, mongoSchema: MongoSchema):

    if isinstance(doc, list):
        return [to_brewtils(value, mongoSchema) for value in doc]

    try:
        if mongoSchema.brewtils_model:

            clean_model = clean_id(doc)

            model = SchemaParser().parse(
                clean_model, mongoSchema.brewtils_model, from_string=False
            )
            return model
    except Exception as e:
        logger.error(f"Failed to load Schema for blob: {doc}")
        raise e

    return doc


def from_brewtils(model: ModelItem | list, mongoSchema: MongoSchema = None):

    if mongoSchema is None:
        mongoSchema = get_collection_schema(model)

    if isinstance(model, list):
        return [from_brewtils(value, mongoSchema) for value in model]

    if mongoSchema and mongoSchema.mongo_schema:
        raw_dict = mongoSchema.mongo_schema().dump(model)
        return clean_id(raw_dict, to_mongo=True)

    else:
        return clean_id(raw_dict, to_mongo=True)


async def update(update: ModelType) -> Optional[ModelItem]:
    """Update a single document

    Args:
        collection: Name of collection to modify
        filter: Filter parameters
        update: Update parameter

    Returns:
        None

    """

    schema = get_collection_schema(update)

    update_dict = from_brewtils(update, schema)

    updated_model = await async_db[schema.collection].update_one(
        {"_id": update_dict["_id"]}, {"$set": update_dict}
    )

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

    query = kwargs.get("raw_query", None)

    include_fields = kwargs.get("include_fields", None)
    exclude_fields = kwargs.get("exclude_fields", None)

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

    doc = await async_db[schema.collection].find_one(
        query,
        find_fields,
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
