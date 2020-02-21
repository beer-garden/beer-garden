# -*- coding: utf-8 -*-
import beer_garden.db.mongo.api
from beer_garden.events import publish_event
from brewtils.models import Events

check_connection = beer_garden.db.mongo.api.check_connection
create_connection = beer_garden.db.mongo.api.create_connection
initial_setup = beer_garden.db.mongo.api.initial_setup

count = beer_garden.db.mongo.api.count
query_unique = beer_garden.db.mongo.api.query_unique
query = beer_garden.db.mongo.api.query
reload = beer_garden.db.mongo.api.reload
replace_commands = beer_garden.db.mongo.api.replace_commands


def _create(obj):
    return beer_garden.db.mongo.api.create(obj)


def _update(obj):
    return beer_garden.db.mongo.api.update(obj)


def _delete(obj):
    return beer_garden.db.mongo.api.delete(obj)


create = _create
update = _update
delete = _delete
