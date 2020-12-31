# -*- coding: utf-8 -*-
import json
from inspect import isawaitable

import six

from beer_garden.api.http.filter import model_filter, model_db_filter
from brewtils.models import BaseModel
from brewtils.schema_parser import SchemaParser

import beer_garden.api
import beer_garden.router


class Client(object):
    def __init__(self, filter_calls=None):
        self.filter_calls = filter_calls

    def serialize_helper(self, current_user=None, required_permissions=None):
        return SerializeHelper(
            current_user=current_user,
            required_permissions=required_permissions,
            filter_calls=self.filter_calls,
        )


class SerializeHelper(object):
    def __init__(self, current_user=None, required_permissions=None, filter_calls=None):
        self.current_user = current_user
        self.required_permissions = required_permissions
        self.filter = (
            filter_calls
            and self.required_permissions
            and len(self.required_permissions) > 0
        )

    async def __call__(self, operation, serialize_kwargs=None, **kwargs):

        if self.filter:

            # Run filter to ensure they have the ability to modify the object
            model_filter(
                operation,
                current_user=self.current_user,
                required_permissions=self.required_permissions,
            )

            # Inject additional logic to support database filtering
            model_db_filter(obj=operation, current_user=self.current_user)

        result = beer_garden.router.route(operation, **kwargs)

        # Await any coroutines
        if isawaitable(result):
            result = await result

        if self.filter:

            # Run filter to remove objects they don't have access to
            result = model_filter(
                result,
                current_user=self.current_user,
                required_permissions=self.required_permissions,
            )

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
