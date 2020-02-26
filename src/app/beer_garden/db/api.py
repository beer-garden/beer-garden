# -*- coding: utf-8 -*-
import beer_garden.db.mongo.api

check_connection = beer_garden.db.mongo.api.check_connection
create_connection = beer_garden.db.mongo.api.create_connection
initial_setup = beer_garden.db.mongo.api.initial_setup

count = beer_garden.db.mongo.api.count
query_unique = beer_garden.db.mongo.api.query_unique
query = beer_garden.db.mongo.api.query
reload = beer_garden.db.mongo.api.reload
replace_commands = beer_garden.db.mongo.api.replace_commands
distinct = beer_garden.db.mongo.api.distinct

create = beer_garden.db.mongo.api.create
update = beer_garden.db.mongo.api.update
delete = beer_garden.db.mongo.api.delete
