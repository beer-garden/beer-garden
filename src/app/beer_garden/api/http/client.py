# -*- coding: utf-8 -*-
import asyncio
import json
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

import six
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser

import beer_garden.api
import beer_garden.router


class ExecutorClient(object):
    parser = SchemaParser()
    pool = ThreadPoolExecutor(50)

    async def __call__(self, *args, serialize_kwargs=None, **kwargs):
        result = await asyncio.get_event_loop().run_in_executor(
            self.pool, partial(beer_garden.router.route, *args, **kwargs)
        )

        # Handlers overwhelmingly just write the response so default to serializing
        serialize_kwargs = serialize_kwargs or {}
        if "to_string" not in serialize_kwargs:
            serialize_kwargs["to_string"] = True

        # We're not going to ever double-serialize a string
        if isinstance(result, six.string_types):
            return result

        if self.json_dump(result):
            return json.dumps(result) if serialize_kwargs["to_string"] else result

        return SchemaParser.serialize(result, **(serialize_kwargs or {}))

    @staticmethod
    def json_dump(result) -> bool:
        """Determine whether to just json dump the result"""
        if result is None:
            return True

        if isinstance(result, dict):
            return True

        if isinstance(result, list) and (
            len(result) == 0 or not isinstance(result[0], BaseModel)
        ):
            return True

        return False
