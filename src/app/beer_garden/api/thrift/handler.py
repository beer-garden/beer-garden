# -*- coding: utf-8 -*-
import json
import logging

import mongoengine
import wrapt
from brewtils.errors import (
    ModelValidationError,
    NotFoundError,
    RequestPublishException,
    RestError,
)

import beer_garden
import beer_garden.api
import beer_garden.api.thrift
from beer_garden.api.thrift.client import ThriftClient
from beer_garden.db.mongo.parser import MongoParser

logger = logging.getLogger(__name__)
parser = MongoParser()


def handle_local(namespace):
    # Handle locally if namespace explicitly matches local or if it's empty
    return namespace in (beer_garden.config.get("namespaces.local"), "", None)


def handle_remote(namespace):
    return namespace in beer_garden.api.remote_ns_names()


def namespace_router(_wrapped):
    @wrapt.decorator
    def wrapper(wrapped, _, args, kwargs):
        target_ns = args[0]

        if handle_local(target_ns):
            logger.debug(f"Handling {wrapped.__name__} locally")

            return wrapped(*args[1:], **kwargs)

        if handle_remote(target_ns):
            logger.debug(f"Forwarding {wrapped.__name__} to {target_ns}")

            ns_info = None
            for ns in beer_garden.config.get("namespaces.remote"):
                if ns.name == target_ns:
                    ns_info = ns
                    break

            with ThriftClient(ns_info.host, ns_info.port) as client:
                return getattr(client, wrapped.__name__)(*args)

        raise ValueError(f"Unable to find route to namespace '{target_ns}'")

    return wrapper(_wrapped)


class BartenderHandler(object):
    """Implements the thrift interface."""

    @staticmethod
    def getLocalNamespace():
        return beer_garden.api.get_local_namespace()

    @staticmethod
    def getRemoteNamespaces():
        return beer_garden.api.get_remote_namespaces()

    @staticmethod
    @namespace_router
    def getRequest(request_id):
        return parser.serialize_request(beer_garden.api.get_request(request_id))

    @staticmethod
    @namespace_router
    def getRequests(query):
        return json.dumps(beer_garden.api.get_requests(**json.loads(query)))

    @staticmethod
    @namespace_router
    def processRequest(request, wait_timeout):
        """Validates and publishes a Request.

        :param str request: The Request to process
        :raises InvalidRequest: If the Request is invalid in some way
        :return: None
        """
        try:
            return parser.serialize_request(
                beer_garden.api.process_request(
                    parser.parse_request(request, from_string=True), wait_timeout
                )
            )
        except RequestPublishException as ex:
            raise beer_garden.api.thrift.bg_thrift.PublishException(str(ex))
        except (mongoengine.ValidationError, ModelValidationError, RestError) as ex:
            raise beer_garden.api.thrift.bg_thrift.InvalidRequest("", str(ex))

    @staticmethod
    @namespace_router
    def updateRequest(request_id, patch):
        parsed_patch = parser.parse_patch(patch, many=True, from_string=True)

        return parser.serialize_request(
            beer_garden.api.update_request(request_id, parsed_patch)
        )

    @staticmethod
    @namespace_router
    def getInstance(instance_id):
        return parser.serialize_instance(beer_garden.api.get_instance(instance_id))

    @staticmethod
    @namespace_router
    def initializeInstance(instance_id):
        """Initializes an instance.

        :param instance_id: The ID of the instance
        :return: QueueInformation object describing message queue for this system
        """
        try:
            instance = beer_garden.api.initialize_instance(instance_id)
        except mongoengine.DoesNotExist:
            raise beer_garden.api.thrift.bg_thrift.InvalidSystem(
                "", f"Database error initializing instance {instance_id}"
            ) from None

        return parser.serialize_instance(instance, to_string=True)

    @staticmethod
    @namespace_router
    def updateInstance(instance_id, patch):
        parsed_patch = parser.parse_patch(patch, many=True, from_string=True)

        return parser.serialize_instance(
            beer_garden.api.update_instance(instance_id, parsed_patch)
        )

    @staticmethod
    @namespace_router
    def startInstance(instance_id):
        """Starts an instance.

        :param instance_id: The ID of the instance
        :return: None
        """
        try:
            instance = beer_garden.api.start_instance(instance_id)
        except mongoengine.DoesNotExist:
            raise beer_garden.api.thrift.bg_thrift.InvalidSystem(
                "", f"Couldn't find instance {instance_id}"
            ) from None

        return parser.serialize_instance(instance, to_string=True)

    @staticmethod
    @namespace_router
    def stopInstance(instance_id):
        """Stops an instance.

        :param instance_id: The ID of the instance
        :return: None
        """
        try:
            instance = beer_garden.api.stop_instance(instance_id)
        except mongoengine.DoesNotExist:
            raise beer_garden.api.thrift.bg_thrift.InvalidSystem(
                "", f"Couldn't find instance {instance_id}"
            ) from None

        return parser.serialize_instance(instance, to_string=True)

    @staticmethod
    @namespace_router
    def updateInstanceStatus(instance_id, new_status):
        """Update instance status.

        Args:
            instance_id: The instance ID
            new_status: The new status

        Returns:

        """
        try:
            instance = beer_garden.api.update_instance_status(instance_id, new_status)
        except mongoengine.DoesNotExist:
            raise beer_garden.api.thrift.bg_thrift.InvalidSystem(
                instance_id, f"Couldn't find instance {instance_id}"
            ) from None

        return parser.serialize_instance(instance, to_string=True)

    @staticmethod
    @namespace_router
    def removeInstance(instance_id):
        """Removes an instance.

        :param instance_id: The ID of the instance
        :return: None
        """
        try:
            beer_garden.api.remove_instance(instance_id)
        except mongoengine.DoesNotExist:
            raise beer_garden.api.thrift.bg_thrift.InvalidSystem(
                instance_id, f"Couldn't find instance {instance_id}"
            ) from None

    @staticmethod
    @namespace_router
    def getSystem(system_id, include_commands):
        serialize_params = {} if include_commands else {"exclude": {"commands"}}

        return parser.serialize_system(
            beer_garden.api.get_system(system_id), **serialize_params
        )

    @staticmethod
    @namespace_router
    def querySystems(
        filter_params=None,
        order_by=None,
        include_fields=None,
        exclude_fields=None,
        dereference_nested=None,
    ):
        # This is gross, but do it this way so we don't re-define default arg values
        # aka, only pass what what's non-None to systems.query_systems
        query_params = {"filter_params": filter_params}
        for p in ["order_by", "include_fields", "exclude_fields", "dereference_nested"]:
            value = locals()[p]
            if value:
                query_params[p] = value

        serialize_params = {"to_string": True, "many": True}
        if include_fields:
            serialize_params["only"] = include_fields
        if exclude_fields:
            serialize_params["exclude"] = exclude_fields

        return parser.serialize_system(
            beer_garden.api.query_systems(**query_params), **serialize_params
        )

    @staticmethod
    @namespace_router
    def createSystem(system):
        try:
            return parser.serialize_system(
                beer_garden.api.create_system(
                    parser.parse_system(system, from_string=True)
                )
            )
        except mongoengine.errors.NotUniqueError:
            raise beer_garden.api.thrift.bg_thrift.ConflictException(
                "System already exists"
            ) from None

    @staticmethod
    @namespace_router
    def updateSystem(system_id, operations):
        return parser.serialize_system(
            beer_garden.api.update_system(
                system_id, parser.parse_patch(operations, many=True, from_string=True)
            )
        )

    @staticmethod
    @namespace_router
    def reloadSystem(system_id):
        """Reload a system configuration

        :param system_id: The system id
        :return None
        """
        try:
            beer_garden.api.reload_system(system_id)
        except mongoengine.DoesNotExist:
            raise beer_garden.api.thrift.bg_thrift.InvalidSystem(
                "", f"Couldn't find system {system_id}"
            ) from None

    @staticmethod
    @namespace_router
    def removeSystem(system_id):
        """Removes a system from the registry if necessary.

        :param system_id: The system id
        :return:
        """
        try:
            beer_garden.api.remove_system(system_id)
        except mongoengine.DoesNotExist:
            raise beer_garden.api.thrift.bg_thrift.InvalidSystem(
                system_id, f"Couldn't find system {system_id}"
            ) from None

    @staticmethod
    @namespace_router
    def rescanSystemDirectory():
        """Scans plugin directory and starts any new Systems"""
        beer_garden.api.rescan_system_directory()

    @staticmethod
    @namespace_router
    def getQueueMessageCount(queue_name):
        """Gets the size of a queue

        :param queue_name: The queue name
        :return: number of messages currently on the queue
        :raises Exception: If queue does not exist
        """
        return beer_garden.api.get_queue_message_count(queue_name)

    @staticmethod
    @namespace_router
    def getAllQueueInfo():
        return parser.serialize_queue(
            beer_garden.api.get_all_queue_info(), to_string=True, many=True
        )

    @staticmethod
    @namespace_router
    def clearQueue(queue_name):
        """Clear all Requests in the given queue

        Will iterate through all requests on a queue and mark them as "CANCELED".

        :param queue_name: The queue to clean
        :raises InvalidSystem: If the system_name/instance_name does not match a queue
        """
        try:
            beer_garden.api.clear_queue(queue_name)
        except NotFoundError as ex:
            raise beer_garden.api.thrift.bg_thrift.InvalidSystem(queue_name, str(ex))

    @staticmethod
    @namespace_router
    def clearAllQueues():
        """Clears all queues that Bartender knows about"""
        beer_garden.api.clear_all_queues()

    @staticmethod
    @namespace_router
    def getJob(job_id):
        return parser.serialize_job(beer_garden.api.get_job(job_id))

    @staticmethod
    @namespace_router
    def getJobs(filter_params):
        return parser.serialize_job(beer_garden.api.get_jobs(filter_params), many=True)

    @staticmethod
    @namespace_router
    def createJob(job):
        return parser.serialize_job(
            beer_garden.api.create_job(parser.parse_job(job, from_string=True))
        )

    @staticmethod
    @namespace_router
    def pauseJob(job_id):
        return parser.serialize_job(beer_garden.api.pause_job(job_id))

    @staticmethod
    @namespace_router
    def resumeJob(job_id):
        return parser.serialize_job(beer_garden.api.resume_job(job_id))

    @staticmethod
    @namespace_router
    def removeJob(job_id):
        beer_garden.api.remove_job(job_id)

    @staticmethod
    @namespace_router
    def getCommand(command_id):
        return parser.serialize_command(beer_garden.api.get_command(command_id))

    @staticmethod
    @namespace_router
    def getCommands():
        return parser.serialize_command(beer_garden.api.get_commands(), many=True)

    @staticmethod
    @namespace_router
    def getPluginLogConfig(system_name):
        return parser.serialize_logging_config(
            beer_garden.api.get_plugin_log_config(system_name)
        )

    @staticmethod
    @namespace_router
    def reloadPluginLogConfig():
        return parser.serialize_logging_config(
            beer_garden.api.reload_plugin_log_config()
        )

    @staticmethod
    @namespace_router
    def getVersion():
        """Gets the current version of the backend"""
        return beer_garden.api.get_version()
