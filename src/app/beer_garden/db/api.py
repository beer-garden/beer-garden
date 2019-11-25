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


@publish_event(Events.DB_CREATE)
def create_function(obj):
    return beer_garden.db.mongo.api.create(obj)


@publish_event(Events.DB_CREATE)
def update_function(obj):
    return beer_garden.db.mongo.api.update(obj)


@publish_event(Events.DB_DELETE)
def delete_function(obj):
    return beer_garden.db.mongo.api.delete(obj)


create = create_function
update = update_function
delete = delete_function
