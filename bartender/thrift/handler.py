"""Bartender side of the thrift interface."""

import mongoengine

import bartender
import bg_utils
from bartender.instances import initialize_instance, start_instance, stop_instance
from bartender.queues import (
    clear_all_queues,
    clear_queue,
    get_all_queue_info,
    get_queue_message_count,
)
from bartender.requests import process_request
from bartender.systems import reload_system, remove_system, rescan_system_directory
from bg_utils.mongo.parser import MongoParser
from brewtils.errors import (
    ModelValidationError,
    NotFoundError,
    RequestPublishException,
    RestError,
)


class BartenderHandler(object):
    """Implements the thrift interface."""

    def __init__(self):
        self.parser = MongoParser()

    def processRequest(self, request):
        """Validates and publishes a Request.

        :param str request: The Request to process
        :raises InvalidRequest: If the Request is invalid in some way
        :return: None
        """
        try:
            return self.parser.serialize_request(
                process_request(self.parser.parse_request(request, from_string=True))
            )
        except RequestPublishException as ex:
            raise bg_utils.bg_thrift.PublishException(str(ex))
        except (mongoengine.ValidationError, ModelValidationError, RestError) as ex:
            raise bg_utils.bg_thrift.InvalidRequest("", str(ex))

    def initializeInstance(self, instance_id):
        """Initializes an instance.

        :param instance_id: The ID of the instance
        :return: QueueInformation object describing message queue for this system
        """
        try:
            instance = initialize_instance(instance_id)
        except mongoengine.DoesNotExist:
            raise bg_utils.bg_thrift.InvalidSystem(
                "", f"Database error initializing instance {instance_id}"
            )

        return self.parser.serialize_instance(instance, to_string=True)

    def startInstance(self, instance_id):
        """Starts an instance.

        :param instance_id: The ID of the instance
        :return: None
        """
        try:
            instance = start_instance(instance_id)
        except mongoengine.DoesNotExist:
            raise bg_utils.bg_thrift.InvalidSystem(
                "", f"Couldn't find instance {instance_id}"
            )

        return self.parser.serialize_instance(instance, to_string=True)

    def stopInstance(self, instance_id):
        """Stops an instance.

        :param instance_id: The ID of the instance
        :return: None
        """
        try:
            instance = stop_instance(instance_id)
        except mongoengine.DoesNotExist:
            raise bg_utils.bg_thrift.InvalidSystem(
                "", f"Couldn't find instance {instance_id}"
            )

        return self.parser.serialize_instance(instance, to_string=True)

    def reloadSystem(self, system_id):
        """Reload a system configuration

        :param system_id: The system id
        :return None
        """
        try:
            reload_system(system_id)
        except mongoengine.DoesNotExist:
            raise bg_utils.bg_thrift.InvalidSystem(
                "", f"Couldn't find system {system_id}"
            )

    def removeSystem(self, system_id):
        """Removes a system from the registry if necessary.

        :param system_id: The system id
        :return:
        """
        try:
            remove_system(system_id)
        except mongoengine.DoesNotExist:
            raise bg_utils.bg_thrift.InvalidSystem(
                "", f"Couldn't find system {system_id}"
            )

    def rescanSystemDirectory(self):
        """Scans plugin directory and starts any new Systems"""
        rescan_system_directory()

    def getAllQueueInfo(self):
        return self.parser.serialize_queue(
            get_all_queue_info(), to_string=True, many=True
        )

    @staticmethod
    def getQueueMessageCount(queue_name):
        """Gets the size of a queue

        :param queue_name: The queue name
        :return: number of messages currently on the queue
        :raises Exception: If queue does not exist
        """
        return get_queue_message_count(queue_name)

    def clearQueue(self, queue_name):
        """Clear all Requests in the given queue

        Will iterate through all requests on a queue and mark them as "CANCELED".

        :param queue_name: The queue to clean
        :raises InvalidSystem: If the system_name/instance_name does not match a queue
        """
        try:
            clear_queue(queue_name)
        except NotFoundError as ex:
            raise bg_utils.bg_thrift.InvalidSystem(queue_name, str(ex))

    def clearAllQueues(self):
        """Clears all queues that Bartender knows about.

        :return: None
        """
        try:
            clear_all_queues()
        except NotFoundError as ex:
            raise bg_utils.bg_thrift.InvalidSystem("", str(ex))

    def getVersion(self):
        """Gets the current version of the backend"""
        return bartender.__version__
