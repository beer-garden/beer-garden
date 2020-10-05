# -*- coding: utf-8 -*-
import beer_garden.db.mongo.api

from_brewtils = beer_garden.db.mongo.api.from_brewtils
to_brewtils = beer_garden.db.mongo.api.to_brewtils

check_connection = beer_garden.db.mongo.api.check_connection
create_connection = beer_garden.db.mongo.api.create_connection
initial_setup = beer_garden.db.mongo.api.initial_setup

get_pruner = beer_garden.db.mongo.api.get_pruner
prune_tasks = beer_garden.db.mongo.api.prune_tasks

get_job_store = beer_garden.db.mongo.api.get_job_store

count = beer_garden.db.mongo.api.count
query_unique = beer_garden.db.mongo.api.query_unique
query = beer_garden.db.mongo.api.query
reload = beer_garden.db.mongo.api.reload
distinct = beer_garden.db.mongo.api.distinct

create = beer_garden.db.mongo.api.create
update = beer_garden.db.mongo.api.update
modify = beer_garden.db.mongo.api.modify
delete = beer_garden.db.mongo.api.delete
