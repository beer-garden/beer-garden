# -*- coding: utf-8 -*-
import json
from inspect import isawaitable

import six

from beer_garden.api.http.authorization import PermissionRequiredAccess
from beer_garden.plugin import _from_kwargs
from beer_garden.requests import get_request
from beer_garden.scheduler import get_job
from beer_garden.systems import get_system
from brewtils.errors import RequestForbidden
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
            filter_models(
                operation,
                current_user=self.current_user,
                required_permissions=self.required_permissions,
            )

        result = beer_garden.router.route(operation, **kwargs)

        # Await any coroutines
        if isawaitable(result):
            result = await result

        if self.filter:
            result = filter_models(
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


def filter_models(
    obj, raise_error=True, current_user=None, required_permissions=list()
):
    # If permissions are not set, then don't filter
    if not required_permissions or len(required_permissions) == 0:
        return obj

    if not current_user:
        raise RequestForbidden("Action requires the User to be logged in")

    # Local Admins get everything by default
    for permission in current_user.permissions:
        if permission.is_local and permission.access == "ADMIN":
            return obj

    if type(obj) == list:
        new_obj = list()
        for obj_item in obj:
            # For list objects, we will not raise an error message
            obj_item = filter_models(
                obj_item,
                raise_error=False,
                current_user=current_user,
                required_permissions=required_permissions,
            )
            if obj_item:
                new_obj.append(obj_item)
        return new_obj

    obj_namespace = None
    if not hasattr(obj, "schema"):
        return obj
    # if type(obj) != BaseModel:
    #     # We don't know how to filter this
    #     return obj
    else:
        if obj.schema in ["RequestSchema", "SystemSchema"]:
            obj_namespace = obj.namespace
        elif obj.schema == "JobSchema":
            obj_namespace = obj.request_template.namespace
        elif obj.schema == "InstanceSchema":
            system, _ = _from_kwargs(instance=obj)
            obj_namespace = system.namespace

        elif obj.schema == "QueueSchema":
            system = get_system(obj.system_id)
            obj_namespace = system.namespace

        elif obj.schema == "PrincipalSchema":
            # Only local admins get this object and it was already checked for above
            # So we want to invoke the failure use case
            obj_namespace = None

        # We won't know the System ID, so we have to assume we can't check this
        elif obj.schema == "CommandSchema":
            return obj

        elif obj.schema == "EventSchema":
            if obj.payload:
                filter_models(
                    obj.payload,
                    current_user=current_user,
                    required_permissions=required_permissions,
                    raise_error=raise_error,
                )

        elif obj.schema == "OperationSchema":
            if obj.model:
                filter_models(
                    obj.model,
                    current_user=current_user,
                    required_permissions=required_permissions,
                    raise_error=raise_error,
                )
            elif "REQUEST_COUNT" == obj.operation_type:
                if "namespace__nin" not in obj.kwargs:
                    obj.kwargs["namespace__nin"] = list()
                for permission in current_user.permissions:
                    obj.kwargs["namespace__nin"].append(permission.namespace)
            elif "READ" not in obj.operation_type:
                if "REQUEST" in obj.operation_type:
                    request_id = None
                    if len(obj.arg) > 0:
                        request_id = obj.args[0]
                    elif "request_id" in obj.kwargs:
                        request_id = obj.kwargs["request_id"]
                    if request_id:
                        request = get_request(request_id)
                        obj.kwargs["request"] = request
                        obj_namespace = request.namespace
                elif "SYSTEM" in obj.operation_type:
                    system_id = None
                    if len(obj.arg) > 0:
                        system_id = obj.args[0]
                    elif "system_id" in obj.kwargs:
                        system_id = obj.kwargs["system_id"]
                    if system_id:
                        system = get_system(system_id)
                        obj.kwargs["system"] = system
                        obj_namespace = system.namespace

                elif "INSTANCE" in obj.operation_type:
                    instance_id = None
                    if len(obj.arg) > 0:
                        instance_id = obj.args[0]
                    elif "instance_id" in obj.kwargs:
                        instance_id = obj.kwargs["instance_id"]
                    if instance_id:
                        system, _ = _from_kwargs(instance_id=instance_id)
                        obj.kwargs["system"] = system
                        obj_namespace = system.namespace
                elif "JOB" in obj.operation_type:
                    job_id = None
                    if len(obj.arg) > 0:
                        job_id = obj.args[0]
                    elif "job_id" in obj.kwargs:
                        job_id = obj.kwargs["job_id"]
                    if job_id:
                        job = get_job(job_id)
                        obj_namespace = job.request_template.namespace
                elif "GARDEN" in obj.operation_type:
                    # This requires local Admin access, should already be handled
                    pass
                elif "PLUGIN" in obj.operation_type:
                    # This requires local Admin access, should already be handled
                    pass
                elif "QUEUE" == obj.operation_type:
                    # This requires local Admin access, should already be handled
                    pass

        else:
            return obj

        if obj_namespace:
            if namespace_check(
                obj_namespace,
                current_user=current_user,
                required_permissions=required_permissions,
            ):
                return obj
            if raise_error:
                raise RequestForbidden("Action requires permissions %s" % obj_namespace)
        else:
            return obj
        return None


def namespace_check(namespace, current_user=None, required_permissions=list()):
    for permission in current_user.permissions:
        for required in required_permissions:
            if permission.access in PermissionRequiredAccess[required] and (
                permission.namespace == namespace or permission.is_local
            ):
                return True

    return False
