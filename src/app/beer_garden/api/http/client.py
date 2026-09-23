# -*- coding: utf-8 -*-
import json
from inspect import isawaitable
from typing import Any, Optional

import elasticapm
from brewtils.models import BaseModel, Operation, User, Request
from brewtils.schema_parser import SchemaParser
from asyncio import Future
import beer_garden.api
import beer_garden.config as config
import beer_garden.router
from beer_garden.authorization import ModelFilter
from beer_garden.metrics import CollectMetrics, extract_custom_context
from beer_garden.api.http.base_handler import future_wait
import logging

logger = logging.getLogger(__name__)

class SerializeHelper(object):
    def __init__(self):
        self.model_filter = ModelFilter()

    def remap_garden_operation(self, operation: Operation):

        # TODO: Update to actual release version
        logger.error("Mapping over operation to Gardeen Request")
        garden_request = Operation(
            operation_type="REQUEST_CREATE",
            target_garden_name=operation.target_garden_name,
            model=Request(
                command_type="GARDEN",
                hidden=True,
                parameters={
                    "operation": SchemaParser.serialize_operation(
                        operation, to_string=False
                    )
                },
            ),
            model_type="Request",
        )

        return garden_request

    async def __call__(
        self,
        operation: Operation,
        serialize_kwargs=None,
        current_user: User = None,
        minimum_permission: str = None,
        filter_results: bool = True,
        **kwargs,
    ):
        wait_event = None
        if operation.target_garden_name != None and operation.target_garden_name != config.get("garden.name"):
            if operation.operation_type != "REQUEST_CREATE":
                new_operation = self.remap_garden_operation(operation)           
                try:
                    wait_event = Future()
                    new_operation.kwargs["wait_event"] = wait_event
                    operation = new_operation
                except RuntimeError:
                    logger.error("Failed to create future for mapped operation")
                    pass

        trace_parent_header = None
        if hasattr(operation, "metadata") and "_trace_parent" in operation.metadata:
            trace_parent_header = operation.metadata["_trace_parent"]
        elif (
            hasattr(operation, "payload")
            and hasattr(operation.payload, "metadata")
            and "_trace_parent" in operation.payload.metadata
        ):
            trace_parent_header = operation.payload.metadata["_trace_parent"]

        with CollectMetrics(
            "API",
            f"API::{operation.operation_type}",
            trace_parent_header=trace_parent_header,
        ):

            if config.get("metrics.elastic.enabled") and current_user:
                elasticapm.set_user_context(
                    username=current_user.username, user_id=current_user.id
                )

                if "REQUEST" in operation.operation_type:
                    if (
                        hasattr(operation, "model")
                        and hasattr(operation.model, "metadata")
                        and "_trace_parent" not in operation.model.metadata
                    ):
                        operation.model.metadata["_trace_parent"] = (
                            trace_parent_header
                            if trace_parent_header
                            else elasticapm.get_trace_parent_header()
                        )

            operation.source_api = "HTTP"
            result = beer_garden.router.route(operation)

            # Await any coroutines
            if isawaitable(result):
                result = await result

            if wait_event is not None:
                logger.error("Waiting for operation to return")
                await future_wait(wait_event, 60)
                result = wait_event.result().output

            if filter_results and minimum_permission and current_user:
                result = self.model_filter.filter_object(
                    user=current_user, permission=minimum_permission, obj=result
                )

            if config.get("metrics.elastic.enabled"):
                extract_custom_context(result)

            # Handlers overwhelmingly just write the response so default to serializing
            serialize_kwargs = serialize_kwargs or {}
            if "to_string" not in serialize_kwargs:
                serialize_kwargs["to_string"] = True

            # Don't serialize if that's not desired
            if serialize_kwargs.get("return_raw") or isinstance(result, str):
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
