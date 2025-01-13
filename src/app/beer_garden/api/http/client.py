# -*- coding: utf-8 -*-
import json
from inspect import isawaitable
from typing import Any, Optional

import elasticapm
import six
from brewtils.models import BaseModel, Operation, User
from brewtils.schema_parser import SchemaParser

import beer_garden.api
import beer_garden.router
from beer_garden.authorization import ModelFilter
from beer_garden.metrics import extract_custom_context, get_apm_client


class SerializeHelper(object):
    def __init__(self):
        self.model_filter = ModelFilter()

    async def __call__(
        self,
        operation: Operation,
        serialize_kwargs=None,
        current_user: User = None,
        minimum_permission: str = None,
        filter_results: bool = True,
        **kwargs,
    ):

        client = get_apm_client("API", f"API::{operation.operation_type}")

        if client:
            # extract_custom_context(operation)
            
            operation.metadata = {"_trace_parent": elasticapm.get_trace_parent_header()}
            if current_user:
                elasticapm.set_user_context(
                    username=current_user.username, user_id=current_user.id
                )

        operation.source_api = "HTTP"
        result = beer_garden.router.route(operation)

        # Await any coroutines
        if isawaitable(result):
            result = await result

        if filter_results and minimum_permission and current_user:
            result = self.model_filter.filter_object(
                user=current_user, permission=minimum_permission, obj=result
            )

        if client:
            extract_custom_context(result)
            client.end_transaction(result="success")

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
