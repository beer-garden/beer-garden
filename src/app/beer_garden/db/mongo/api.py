# -*- coding: utf-8 -*-
from typing import List, Optional, Type, Union

import brewtils.models
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser
from mongoengine import DoesNotExist

import beer_garden.db.mongo.models
from beer_garden.db.mongo.models import MongoModel
from beer_garden.db.mongo.parser import MongoParser

ModelType = Union[
    Type[brewtils.models.Command],
    Type[brewtils.models.Instance],
    Type[brewtils.models.Job],
    Type[brewtils.models.Request],
    Type[brewtils.models.RequestTemplate],
    Type[brewtils.models.System],
]

ModelItem = Union[
    brewtils.models.Command,
    brewtils.models.Instance,
    brewtils.models.Job,
    brewtils.models.Request,
    brewtils.models.RequestTemplate,
    brewtils.models.System,
]

_model_map = {}
for model_name in beer_garden.db.mongo.models.__all__:
    mongo_class = getattr(beer_garden.db.mongo.models, model_name)
    _model_map[mongo_class.brewtils_model] = mongo_class


def from_brewtils(obj: ModelItem) -> MongoModel:
    model_dict = SchemaParser.serialize(obj, to_string=False)
    mongo_obj = MongoParser.parse(model_dict, type(obj), from_string=False)
    return mongo_obj


def to_brewtils(
    obj: Union[MongoModel, List[MongoModel]]
) -> Union[ModelItem, List[ModelItem]]:
    if obj is None or (isinstance(obj, list) and len(obj) == 0):
        return obj

    serialized = MongoParser.serialize(obj, to_string=False)
    many = True if isinstance(serialized, list) else False
    model_class = obj[0].brewtils_model if many else obj.brewtils_model

    return SchemaParser.parse(serialized, model_class, from_string=False, many=many)


def count(model_class: ModelType, **kwargs) -> int:
    for k, v in kwargs.items():
        if isinstance(v, BaseModel):
            kwargs[k] = from_brewtils(v)

    query_set = _model_map[model_class].objects(**kwargs)
    return query_set.count()


def query_unique(model_class: ModelType, **kwargs) -> Optional[ModelItem]:
    try:
        for k, v in kwargs.items():
            if isinstance(v, BaseModel):
                kwargs[k] = from_brewtils(v)

        query_set = _model_map[model_class].objects.get(**kwargs)
        return to_brewtils(query_set)
    except DoesNotExist:
        return None


def query(model_class: ModelType, **kwargs) -> List[ModelItem]:
    """Query a collection

    It's possible to specify `include_fields` _and_ `exclude_fields`. This doesn't make
    a lot of sense, but you can do it. If the same field is in both `exclude_fields`
    takes priority (the field will NOT be included in the response).

    Args:
        model_class: The Brewtils model class to query for
        **kwargs: Arguments to control the query. Valid options are:
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
    query_set = _model_map[model_class].objects

    if kwargs.get("filter_params"):
        filter_params = kwargs["filter_params"]

        if "parent" in filter_params:
            filter_params["parent"] = from_brewtils(filter_params["parent"])

        query_set = query_set.filter(**(kwargs.get("filter_params", {})))

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


def create(obj: ModelItem) -> ModelItem:
    mongo_obj = from_brewtils(obj)

    if hasattr(mongo_obj, "deep_save"):
        mongo_obj.deep_save()
    else:
        mongo_obj.save()

    return to_brewtils(mongo_obj)


def update(obj: ModelItem) -> ModelItem:
    return create(obj)


def delete(obj: ModelItem) -> None:
    mongo_obj = from_brewtils(obj)

    if hasattr(mongo_obj, "deep_delete"):
        mongo_obj.deep_delete()
    else:
        mongo_obj.delete()


def reload(obj: ModelItem) -> ModelItem:
    existing_obj = _model_map[type(obj)].objects.get(id=obj.id)

    return to_brewtils(existing_obj)
