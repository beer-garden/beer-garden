# -*- coding: utf-8 -*-
import json
from inspect import isawaitable
from typing import Any, Optional

import six
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser

import beer_garden.api
import beer_garden.router


class SerializeHelper(object):
    async def __call__(self, *args, serialize_kwargs=None, **kwargs):
        result = beer_garden.router.route(*args, **kwargs)

        # Await any coroutines
        if isawaitable(result):
            result = await result

        # Handlers overwhelmingly just write the response so default to serializing
        serialize_kwargs = serialize_kwargs or {}
        if "to_string" not in serialize_kwargs:
            serialize_kwargs["to_string"] = True

        # Don't serialize if that's not desired
        if serialize_kwargs.get("return_raw") or isinstance(result, six.string_types):
            return result

        if self.json_dump(result):
            return json.dumps(result) if serialize_kwargs["to_string"] else result

        return SchemaParser.serialize(result, **(serialize_kwargs or {}))

    @staticmethod
    def json_dump(result: Optional[Any]) -> bool:
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
