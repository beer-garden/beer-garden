# -*- coding: utf-8 -*-
from brewtils.models import Event

from beer_garden.db.mongo.models import Request


class TestSendEventToParent(object):
    event = Event(
        payload_type="Request",
        payload=Request(
            system="system_test",
            command="command_test",
            namespace="test",
        ),
    )

    def config_get(self, config_name):
        return []
