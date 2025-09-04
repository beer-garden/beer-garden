# -*- coding: utf-8 -*-
from typing import Optional, Union

from box import Box
from brewtils.models import BaseModel
from bson import ObjectId
from mongoengine import Document
from mongoengine.queryset.visitor import Q, QCombination
from motor import MotorDatabase
from motor.motor_tornado import MotorClient

import beer_garden.db.mongo.api as api

motor_db: Optional[MotorDatabase] = None

# General note for ASYNC usage. Only use async function for READ operations.
# WRITE operations should still use the synchronous mongoengine functions
# because mongoengine handles some additional logic in the pre_save and
# post_save operations that we want to keep.


def create_connection(db_config: Box = None) -> None:
    """Register a database connection

    Args:
        db_config: Yapconf-generated configuration object

    Returns:
        None
    """
    global motor_db

    motor_conn = MotorClient(
        host=db_config.connection.host,
        port=db_config.connection.port,
    )
    motor_db = motor_conn[db_config.name]


async def query_async(
    model_class, q_filter: Union[Q, QCombination, None] = None, **kwargs
):

    query_info = {}
    query_set = api._model_map[model_class].objects

    if q_filter:
        query_set = query_set.filter(q_filter)

    if kwargs.get("filter_params"):
        filter_params = kwargs["filter_params"]

        # If any values are brewtils models those need to be converted
        for key in filter_params:
            if isinstance(filter_params[key], BaseModel):
                filter_params[key] = api.from_brewtils(filter_params[key])

        query_set = query_set.filter(**(kwargs.get("filter_params", {})))

    # Bad things happen if you try to use a hint with a text search.
    if kwargs.get("text_search"):
        query_set = query_set.search_text(kwargs.get("text_search"))
    elif kwargs.get("hint"):
        # Sanity check - if index is 'bad' just let mongo deal with it
        if kwargs.get("hint") in api._model_map[model_class].index_names():
            query_info["hint"] = kwargs.get("hint")

    if kwargs.get("include_fields"):
        query_info["projection"] = {
            field.replace("__", "."): True for field in kwargs.get("include_fields")
        }

    elif kwargs.get("exclude_fields"):
        query_info["projection"] = {
            field.replace("__", "."): False for field in kwargs.get("exclude_fields")
        }

    if kwargs.get("start"):
        query_info["skip"] = int(kwargs.get("start"))

    if kwargs.get("length"):
        query_info["limit"] = int(kwargs.get("length"))

    query_info["filter"] = query_set._query

    cursor = motor_db[api._model_map[model_class]._get_collection_name()].find(
        **query_info
    )

    if kwargs.get("order_by"):
        if kwargs.get("order_by")[0] == "-":
            cursor.sort(kwargs.get("order_by")[1:], -1)
        else:
            cursor.sort(kwargs.get("order_by")[1:], 1)

    results = []

    for document in await cursor.to_list(length=None):
        if "_id" in document:
            document["id"] = str(document["_id"])
            del document["_id"]

        mongoengine_model = api._model_map[model_class](**document)
        results.append(
            api.to_brewtils(
                await dbreference_mapping(
                    mongoengine_model, query_info.get("projection", [])
                )
            )
        )

    return results


async def query_unique_async(model_class, raise_missing=False, **kwargs):
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

    for k, v in kwargs.items():
        if isinstance(v, BaseModel):
            kwargs[k] = api.from_brewtils(v)

    query_info = {}

    if kwargs.get("include_fields"):
        query_info["projection"] = {
            field.replace("__", "."): True for field in kwargs.get("include_fields")
        }

    elif kwargs.get("exclude_fields"):
        query_info["projection"] = {
            field.replace("__", "."): False for field in kwargs.get("exclude_fields")
        }

    del kwargs["include_fields"], kwargs["exclude_fields"]

    if kwargs.get("id"):
        kwargs["_id"] = ObjectId(kwargs.pop("id"))

    query_info["filter"] = kwargs

    document = await motor_db[
        api._model_map[model_class]._get_collection_name()
    ].find_one(**query_info)

    if document is None:
        if raise_missing:
            raise api._model_map[model_class].DoesNotExist(
                f"{model_class.__name__} matching query does not exist."
            )
        return None

    if "_id" in document:
        document["id"] = str(document["_id"])
        del document["_id"]

    mongoengine_model = api._model_map[model_class](**document)

    return api.to_brewtils(
        await dbreference_mapping(mongoengine_model, query_info.get("projection", []))
    )


async def dbreference_mapping(document, projections: dict = None):
    """Recursively map MongoDB DBRef fields to their actual documents"""

    if isinstance(document, Document):
        for field_name in document._fields:
            field = document._fields[field_name]
            value = getattr(document, field_name)

            new_projections = {}
            if projections:
                for item, filter in projections.items():
                    if item.startswith(f"{field_name}."):
                        new_projections[item[len(field_name) + 1 :]] = filter

            if (
                field.__class__.__name__ == "ReferenceField"
                or field.__class__.__name__ == "LazyReferenceField"
            ) and value:
                reference_document = await motor_db[
                    field.document_type._get_collection_name()
                ].find_one(
                    {"_id": ObjectId(value.id)}, projection=new_projections or None
                )

                if "_id" in reference_document:
                    reference_document["id"] = str(reference_document["_id"])
                    del reference_document["_id"]

                mongoengine_model = field.document_type(**reference_document)
                setattr(
                    document,
                    field_name,
                    await dbreference_mapping(mongoengine_model, new_projections),
                )
            elif (
                field.__class__.__name__ == "ListField"
                and (
                    field.field.__class__.__name__ == "ReferenceField"
                    or field.field.__class__.__name__ == "LazyReferenceField"
                )
                and value
            ):
                new_projections = {}
                if projections:
                    for item, filter in projections.items():
                        if item.startswith(f"{field_name}."):
                            new_projections[item[len(field_name) + 1 :]] = filter

                new_list = []

                ids = []

                for item in value:
                    if isinstance(item.id, ObjectId):
                        ids.append(item.id)
                    else:
                        ids.append(ObjectId(item.id))

                if value and ids:

                    cursor = motor_db[
                        field.field.document_type._get_collection_name()
                    ].find({"_id": {"$in": ids}}, projection=new_projections or None)

                    for reference_document in await cursor.to_list(length=None):
                        if reference_document:
                            if "_id" in reference_document:
                                reference_document["id"] = str(
                                    reference_document["_id"]
                                )
                                del reference_document["_id"]

                            mongoengine_model = field.field.document_type(
                                **reference_document
                            )
                            if mongoengine_model:
                                new_list.append(
                                    await dbreference_mapping(
                                        mongoengine_model, new_projections
                                    )
                                )

                setattr(document, field_name, new_list)

    return document


async def query(
    collection: str = None, filter: dict = None, projection: dict = None
) -> dict:
    """Query for a single document

    Args:
        collection: Name of collection to query
        filter: Filter parameters
        projection: Projection parameters

    Returns:
        Dict of the find_one result

    """
    return await motor_db[collection].find_one(filter=filter, projection=projection)


async def update_one(
    collection: str = None, filter: dict = None, update: dict = None
) -> None:
    """Update a single document

    Args:
        collection: Name of collection to modify
        filter: Filter parameters
        update: Update parameter

    Returns:
        None

    """
    return await motor_db[collection].update_one(filter=filter, update=update)
