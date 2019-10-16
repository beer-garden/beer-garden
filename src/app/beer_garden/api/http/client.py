# -*- coding: utf-8 -*-
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

import six
from brewtils.schema_parser import SchemaParser

import beer_garden.api


class ExecutorClient(object):
    parser = SchemaParser()
    pool = ThreadPoolExecutor(50)

    def __getattr__(self, _api):
        return partial(self, _api)

    async def __call__(self, *args, serialize_kwargs=None, **kwargs):
        result = await asyncio.get_event_loop().run_in_executor(
            self.pool, partial(getattr(beer_garden.api, args[0]), *args[1:], **kwargs)
        )

        if isinstance(result, list) and len(result) == 0:
            return "[]"

        if (
            result is None
            or isinstance(result, (six.string_types, dict))
            or (
                isinstance(result, list)
                and isinstance(result[0], (six.string_types, dict))
            )
        ):
            return result

        # HTTP handlers overwhelmingly just write the response, so just serialize here
        serialize_kwargs = serialize_kwargs or {}
        if "to_string" not in serialize_kwargs:
            serialize_kwargs["to_string"] = True

        return SchemaParser.serialize(result, **(serialize_kwargs or {}))
