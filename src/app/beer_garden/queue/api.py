# -*- coding: utf-8 -*-
import beer_garden.queue.rabbit

create_clients = beer_garden.queue.rabbit.create_clients
initial_setup = beer_garden.queue.rabbit.initial_setup

create = beer_garden.queue.rabbit.create
put = beer_garden.queue.rabbit.put
clear = beer_garden.queue.rabbit.clear
remove = beer_garden.queue.rabbit.remove
