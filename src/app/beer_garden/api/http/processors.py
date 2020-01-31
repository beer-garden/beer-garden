# -*- coding: utf-8 -*-
import logging

from brewtils.schema_parser import SchemaParser

import beer_garden.api.http
import beer_garden.api.http.handlers.v1 as v1

logger = logging.getLogger(__name__)


def process(item):
    """Publish to all the Websockets"""
    try:
        # So we're going to need a better way to do this
        if item.payload:
            item.payload = SchemaParser.serialize(item.payload)
        if item.metadata:
            item.metadata = {}

        serialized = SchemaParser.serialize(item, to_string=True)

        beer_garden.api.http.io_loop.add_callback(
            v1.event.EventSocket.publish, serialized
        )
    except Exception as ex:
        logger.exception(f"{ex}")
