import logging
import random
import string
from datetime import datetime
from time import sleep

import mongoengine
from pyrabbit2.http import HTTPError

import bartender
import bartender._version
import bg_utils
from bg_utils.mongo.models import Instance, Request, System, StatusInfo
from bg_utils.pika import get_routing_key, get_routing_keys
from brewtils.errors import ModelValidationError, RestError
from brewtils.schema_parser import SchemaParser


class BartenderHandler(object):
    """Implements the BREWMASTER Thrift interface."""

    def __init__(self, registry, clients, plugin_manager, request_validator):
        self.logger = logging.getLogger(__name__)
        self.registry = registry
        self.clients = clients
        self.plugin_manager = plugin_manager
        self.request_validator = request_validator
        self.parser = SchemaParser()

    def processRequest(self, request_id):
        """Validates and publishes a Request.

        :param str request_id: The ID of the Request to process
        :raises InvalidRequest: If the Request is invalid in some way
        :return: None
        """
        request_id = str(request_id)
        self.logger.info("Processing Request: %s", request_id)

        try:
            request = Request.find_or_none(request_id)
            if request is None:
                raise ModelValidationError(
                    "Could not find request with ID '%s'" % request_id
                )

            # Validates the request based on what is in the database.
            # This includes the validation of the request parameters,
            # systems are there, commands are there etc.
            request = self.request_validator.validate_request(request)
            request.save()

            if not self.clients["pika"].publish_request(
                request, confirm=True, mandatory=True
            ):
                msg = "Error while publishing request to queue (%s[%s]-%s %s)" % (
                    request.system,
                    request.system_version,
                    request.instance_name,
                    request.command,
                )
                raise bg_utils.bg_thrift.PublishException(msg)

        except (mongoengine.ValidationError, ModelValidationError, RestError) as ex:
            self.logger.exception(ex)
            raise bg_utils.bg_thrift.InvalidRequest(request_id, str(ex))

    def initializeInstance(self, instance_id):
        """Initializes an instance.

        :param instance_id: The ID of the instance
        :return: QueueInformation object describing message queue for this system
        """
        instance = self._get_instance(instance_id)
        system = self._get_system(instance)

        self.logger.info(
            "Initializing instance %s[%s]-%s",
            system.name,
            instance.name,
            system.version,
        )

        routing_words = [system.name, system.version, instance.name]
        req_name = get_routing_key(*routing_words)
        req_args = {"durable": True, "arguments": {"x-max-priority": 1}}
        req_queue = self.clients["pika"].setup_queue(req_name, req_args, [req_name])

        routing_words.append(
            "".join(
                random.choice(string.ascii_lowercase + string.digits) for _ in range(10)
            )
        )
        admin_keys = get_routing_keys(*routing_words, is_admin=True)
        admin_args = {"auto_delete": True}
        admin_queue = self.clients["pika"].setup_queue(
            admin_keys[-1], admin_args, admin_keys
        )

        connection = {
            "host": bartender.config.publish_hostname,
            "port": bartender.config.amq.connections.message.port,
            "user": bartender.config.amq.connections.message.user,
            "password": bartender.config.amq.connections.message.password,
            "virtual_host": bartender.config.amq.virtual_host,
            "ssl": {"enabled": bartender.config.amq.connections.message.ssl.enabled},
        }

        instance.status = "INITIALIZING"
        instance.status_info = StatusInfo(heartbeat=datetime.utcnow())
        instance.queue_type = "rabbitmq"
        instance.queue_info = {
            "admin": admin_queue,
            "request": req_queue,
            "connection": connection,
            "url": self.clients["public"].connection_url,
        }
        instance.save()

        # Send a request to start to the plugin on the plugin's admin queue
        self.clients["pika"].start(
            system=system.name, version=system.version, instance=instance.name
        )

        return self.parser.serialize_instance(instance, to_string=True)

    def startInstance(self, instance_id):
        """Starts an instance.

        :param instance_id: The ID of the instance
        :return: None
        """
        instance = self._get_instance(instance_id)
        self.plugin_manager.start_plugin(self._get_plugin_from_instance_id(instance_id))
        return self.parser.serialize_instance(instance, to_string=True)

    def stopInstance(self, instance_id):
        """Stops an instance.

        :param instance_id: The ID of the instance
        :return: None
        """
        instance = self._get_instance(instance_id)
        local_plugin = self._get_plugin_from_instance_id(instance_id)
        if local_plugin:
            self.plugin_manager.stop_plugin(local_plugin)
        else:
            system = self._get_system(instance)

            # This causes the request consumer to terminate itself, which ends the plugin
            self.clients["pika"].stop(
                system=system.name, version=system.version, instance=instance.name
            )

        return self.parser.serialize_instance(instance, to_string=True)

    def restartInstance(self, instance_id):
        """Restarts a System. Currently unused."""
        self.stopInstance(instance_id)
        self.startInstance(instance_id)

    def reloadSystem(self, system_id):
        """Reload a system configuration

        :param system_id: The system id
        :return None
        """
        try:
            system = System.objects.get(id=system_id)

            self.logger.info("Reloading system: %s-%s", system.name, system.version)
            self.plugin_manager.reload_system(system.name, system.version)
        except mongoengine.DoesNotExist:
            raise bg_utils.bg_thrift.InvalidSystem(
                "", "Couldn't find system %s" % system_id
            )

    def removeSystem(self, system_id):
        """Removes a system from the registry if necessary.

        :param system_id: The system id
        :return:
        """
        try:
            system = System.objects.get(id=system_id)
        except mongoengine.DoesNotExist:
            raise bg_utils.bg_thrift.InvalidSystem(
                "", "Couldn't find system %s" % system_id
            )

        # Attempt to stop the plugins
        registered = self.registry.get_plugins_by_system(system.name, system.version)

        # Local plugins get stopped by us
        if registered:
            for plugin in registered:
                self.plugin_manager.stop_plugin(plugin)
                self.registry.remove(plugin.unique_name)

        # Remote plugins get a stop request
        else:
            self.clients["pika"].stop(system=system.name, version=system.version)
            count = 0
            while (
                any(instance.status != "STOPPED" for instance in system.instances)
                and count < bartender.config.plugin.local.timeout.shutdown
            ):
                sleep(1)
                count += 1
                system.reload()

        system.reload()

        # Now clean up the message queues
        for instance in system.instances:

            # It is possible for the request or admin queue to be none if we are
            # stopping an instance that was not properly started.
            request_queue = instance.queue_info.get("request", {}).get("name")
            admin_queue = instance.queue_info.get("admin", {}).get("name")

            self.clients["pyrabbit"].destroy_queue(
                request_queue, force_disconnect=(instance.status != "STOPPED")
            )
            self.clients["pyrabbit"].destroy_queue(
                admin_queue, force_disconnect=(instance.status != "STOPPED")
            )

        # Finally, actually delete the system
        system.deep_delete()

    def rescanSystemDirectory(self):
        """Scans plugin directory and starts any new Systems"""
        self.logger.info("Rescanning system directory.")
        self.plugin_manager.scan_plugin_path()

    def getQueueInfo(self, system_name, system_version, instance_name):
        """Gets the size of a queue

        :param system_name: The system name
        :param system_version: The system version
        :param instance_name: The instance name
        :return size of the queue
        :raises Exception: If queue does not exist
        """
        routing_key = get_routing_key(system_name, system_version, instance_name)
        self.logger.debug("Get the queue state for %s", routing_key)

        return bg_utils.bg_thrift.QueueInfo(
            routing_key, self.clients["pyrabbit"].get_queue_size(routing_key)
        )

    def clearQueue(self, queue_name):
        """Clear all Requests in the given queue

        Will iterate through all requests on a queue and mark them as "CANCELED".

        :param queue_name: The queue to clean
        :raises InvalidSystem: If the system_name/instance_name does not match a queue
        """
        try:
            self.logger.debug("Clearing queue %s", queue_name)
            self.clients["pyrabbit"].clear_queue(queue_name)
        except HTTPError as ex:
            if ex.status == 404:
                raise bg_utils.bg_thrift.InvalidSystem(
                    queue_name, "No queue named %s" % queue_name
                )
            else:
                raise

    def clearAllQueues(self):
        """Clears all queues that Bartender knows about.

        :return: None
        """
        self.logger.debug("Clearing all queues")
        systems = System.objects.all()

        for system in systems:
            for instance in system.instances:
                routing_key = get_routing_key(
                    system.name, system.version, instance.name
                )
                self.clearQueue(routing_key)

    def getVersion(self):
        """Gets the current version of the backend"""
        self.logger.debug("Getting Version")

        return bartender._version.__version__

    def ping(self):
        """A simple Method to test connectivity."""
        self.logger.info("Ping.")

    def _get_plugin_from_instance_id(self, instance_id):
        instance = self._get_instance(instance_id)
        system = self._get_system(instance)
        unique_name = self.registry.get_unique_name(
            system.name, system.version, instance.name
        )

        return self.registry.get_plugin(unique_name)

    @staticmethod
    def _get_instance(instance_id):
        try:
            return Instance.objects.get(id=instance_id)
        except mongoengine.DoesNotExist:
            raise bg_utils.bg_thrift.InvalidSystem(
                "", "Couldn't find instance %s" % instance_id
            )

    @staticmethod
    def _get_system(instance):
        try:
            return System.objects.get(instances__contains=instance)
        except mongoengine.DoesNotExist:
            raise bg_utils.bg_thrift.InvalidSystem(
                "", "Couldn't find system " "with instance %s" % instance.id
            )
