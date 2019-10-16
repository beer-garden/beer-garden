# -*- coding: utf-8 -*-
from typing import Generic, List, NewType, Optional, Type, Union

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
    Type[brewtils.models.Request],
    Type[brewtils.models.System],
]

ModelItem = Union[
    brewtils.models.Command,
    brewtils.models.Instance,
    brewtils.models.Request,
    brewtils.models.System,
]


mongo_map = {
    brewtils.models.Command: beer_garden.db.mongo.models.Command,
    brewtils.models.Instance: beer_garden.db.mongo.models.Instance,
    brewtils.models.Request: beer_garden.db.mongo.models.Request,
    brewtils.models.System: beer_garden.db.mongo.models.System,
}


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


def query(model_class: ModelType, **kwargs) -> List[ModelItem]:
    query_set = mongo_map[model_class].objects

    if kwargs.get("order_by"):
        query_set = query_set.order_by(kwargs.get("order_by"))

    if kwargs.get("include_fields"):
        query_set = query_set.only(*kwargs.get("include_fields"))

    if kwargs.get("exclude_fields"):
        query_set = query_set.exclude(*kwargs.get("exclude_fields"))

    if not kwargs.get("dereference_nested", True):
        query_set = query_set.no_dereference()

    if kwargs.get("filter_params"):
        filter_params = kwargs["filter_params"]

        if "parent" in filter_params:
            filter_params["parent"] = from_brewtils(filter_params["parent"])

        query_set = query_set.filter(**(kwargs.get("filter_params", {})))

    return [] if len(query_set) == 0 else to_brewtils(query_set)


def query_unique(model_class: ModelType, **kwargs) -> Optional[ModelItem]:
    try:
        for k, v in kwargs.items():
            if isinstance(v, BaseModel):
                kwargs[k] = from_brewtils(v)

        query_set = mongo_map[model_class].objects.get(**kwargs)
        return to_brewtils(query_set)
    except DoesNotExist:
        return None


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
    existing_obj = mongo_map[type(obj)].objects.get(id=obj.id)

    return to_brewtils(existing_obj)
