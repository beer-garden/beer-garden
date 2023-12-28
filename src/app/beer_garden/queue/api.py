# -*- coding: utf-8 -*-
import beer_garden.queue.rabbit

check_connection = beer_garden.queue.rabbit.check_connection
create_clients = beer_garden.queue.rabbit.create_clients
create_fanout_client = beer_garden.queue.rabbit.create_fanout_client
initial_setup = beer_garden.queue.rabbit.initial_setup
setup_event_consumer = beer_garden.queue.rabbit.setup_event_consumer
shutdown_event_consumer = beer_garden.queue.rabbit.shutdown_event_consumer

create = beer_garden.queue.rabbit.create
put = beer_garden.queue.rabbit.put
count = beer_garden.queue.rabbit.count
clear = beer_garden.queue.rabbit.clear
remove = beer_garden.queue.rabbit.remove
