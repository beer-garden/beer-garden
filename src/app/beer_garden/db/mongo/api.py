# -*- coding: utf-8 -*-
from typing import List, Optional, Type, Union

import brewtils.models
from box import Box
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser
from mongoengine import connect, register_connection, DoesNotExist
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

import beer_garden.db.mongo.models
from beer_garden.db.mongo.util import check_indexes, ensure_roles, ensure_users
from beer_garden.db.mongo.models import MongoModel
from beer_garden.db.mongo.parser import MongoParser

ModelType = Union[
    Type[brewtils.models.Command],
    Type[brewtils.models.Instance],
    Type[brewtils.models.Job],
    Type[brewtils.models.Request],
    Type[brewtils.models.RequestTemplate],
    Type[brewtils.models.System],
    Type[brewtils.models.Garden],
]

ModelItem = Union[
    brewtils.models.Command,
    brewtils.models.Instance,
    brewtils.models.Job,
    brewtils.models.Request,
    brewtils.models.RequestTemplate,
    brewtils.models.System,
    brewtils.models.Garden,
]

_model_map = {}
for model_name in beer_garden.db.mongo.models.__all__:
    mongo_class = getattr(beer_garden.db.mongo.models, model_name)
    _model_map[mongo_class.brewtils_model] = mongo_class


def from_brewtils(obj: ModelItem) -> MongoModel:
    """Convert an item from its Brewtils model to its  one

    Args:
        obj: The Brewtils model item

    Returns:
        The Mongo model item

    """
    model_dict = SchemaParser.serialize(obj, to_string=False)
    mongo_obj = MongoParser.parse(model_dict, type(obj), from_string=False)
    return mongo_obj


def to_brewtils(
    obj: Union[MongoModel, List[MongoModel]]
) -> Union[ModelItem, List[ModelItem]]:
    """Convert an item from its Mongo model to its Brewtils one

    Args:
        obj: The Mongo model item

    Returns:
        The Brewtils model item

    """
    if obj is None or (isinstance(obj, list) and len(obj) == 0):
        return obj

    serialized = MongoParser.serialize(obj, to_string=False)
    many = True if isinstance(serialized, list) else False
    model_class = obj[0].brewtils_model if many else obj.brewtils_model

    return SchemaParser.parse(serialized, model_class, from_string=False, many=many)


def check_connection(db_config: Box):
    """Check connectivity to the mongo database

    Args:
        db_config: Yapconf-generated configuration object

    Returns:
        bool: True if successful, False otherwise (unable to connect)

    Raises:
        Any mongoengine or pymongo error *except* ConnectionFailure,
        ServerSelectionTimeoutError
    """
    try:
        # Set timeouts here to a low value - we don't want to wait 30
        # seconds if there's no database
        conn = connect(
            alias="aliveness",
            db=db_config["name"],
            socketTimeoutMS=1000,
            serverSelectionTimeoutMS=1000,
            **db_config["connection"]
        )

        # The 'connect' method won't actually fail
        # An exception won't be raised until we actually try to do something
        conn.server_info()

        # Close the aliveness connection - the timeouts are too low
        conn.close()
    except (ConnectionFailure, ServerSelectionTimeoutError):
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
        connection_alias, name=db_config["name"], **db_config["connection"]
    )


def initial_setup(guest_login_enabled):
    """Do everything necessary to ensure the database is in a 'good' state"""

    for doc in (
        beer_garden.db.mongo.models.Job,
        beer_garden.db.mongo.models.Request,
        beer_garden.db.mongo.models.Role,
        beer_garden.db.mongo.models.System,
        beer_garden.db.mongo.models.Principal,
    ):
        check_indexes(doc)

    ensure_roles()
    ensure_users(guest_login_enabled)


def count(model_class: ModelType, **kwargs) -> int:
    """Count the number of items matching a query

    Args:
        model_class: The Brewtils model class to query for
        **kwargs: Arguments to control the query. Equivalent to 'filter_params' from the
            'query' function.

    Returns:
        The number of items

    """
    for k, v in kwargs.items():
        if isinstance(v, BaseModel):
            kwargs[k] = from_brewtils(v)

    query_set = _model_map[model_class].objects(**kwargs)
    return query_set.count()


def query_unique(model_class: ModelType, **kwargs) -> Optional[ModelItem]:
    """Query a collection for a unique item

    This will search a collection for a single specific item. If no item matching the
    kwarg parameters is found it will return None.

    If more than one item matching is found a MultipleObjectsReturned will be raised.

    Args:
        model_class: The Brewtils model class to query for
        **kwargs: Arguments to control the query. Equivalent to 'filter_params' from the
            'query' function.

    Returns:
        A single Brewtils model

    Raises:
        mongoengine.MultipleObjectsReturned: More than one matching item exists

    """
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

        # If any values are brewtils models those need to be converted
        for key in filter_params:
            if isinstance(filter_params[key], BaseModel):
                filter_params[key] = from_brewtils(filter_params[key])

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
    """Save a new item to the database

    If the Mongo model corresponding to the Brewtils model has a "deep_save" method
    then that will be called. Otherwise the normal "save" will be used.

    Args:
        obj: The Brewtils model to save

    Returns:
        The saved Brewtils model

    """
    mongo_obj = from_brewtils(obj)

    if hasattr(mongo_obj, "deep_save"):
        mongo_obj.deep_save()
    else:
        mongo_obj.save()

    return to_brewtils(mongo_obj)


def update(obj: ModelItem) -> ModelItem:
    """Save changes to an item to the database

    Currently this is functionally identical to the "create" function.

    Args:
        obj: The Brewtils model to save

    Returns:
        The saved Brewtils model

    """
    return create(obj)


def delete(obj: ModelItem) -> None:
    """Delete an item from the database

    If the Mongo model corresponding to the Brewtils model has a "deep_delete" method
    then that will be called. Otherwise the normal "delete" will be used.

    Args:
        obj: The Brewtils model to delete

    Returns:
        None

    """
    mongo_obj = from_brewtils(obj)

    if hasattr(mongo_obj, "deep_delete"):
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


def replace_commands(
    system: brewtils.models.System, new_commands: List[brewtils.models.Command]
) -> brewtils.models.System:
    """Replaces a System's Commands

    Assumes the commands passed in are more important than what currently exists in the
    database. It will delete commands that are not part of `new_commands`.

    This calls the Mongo object methods directly to avoid problems with translating the
    Command.system field.

    Args:
        system: System to update
        new_commands: List of new commands

    Returns:
        The updated Brewtils System
    """
    mongo_system = from_brewtils(system)
    mongo_commands = [from_brewtils(command) for command in new_commands]

    old_commands = beer_garden.db.mongo.models.Command.objects(system=mongo_system)
    old_names = {command.name: command.id for command in old_commands}

    new_names = [command.name for command in new_commands]

    # If this command is already in the DB we want to preserve the ID
    for command in mongo_commands:
        if command.name in old_names:
            command.id = old_names[command.name]

        command.system = mongo_system
        command.save()

    # Clean up orphan commands
    for command in old_commands:
        if command.name not in new_names:
            command.delete()

    mongo_system.commands = mongo_commands
    mongo_system.save()

    return to_brewtils(mongo_system)
