import logging

from datetime import datetime, timedelta
from bg_utils.mongo.models import Instance, Request
from brewtils.stoppable_thread import StoppableThread


class PluginStatusMonitor(StoppableThread):
    """Monitor plugin heartbeats and update plugin status"""

    def __init__(self, clients, heartbeat_interval=10, timeout_seconds=30):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Plugin Status Monitor"
        self.clients = clients
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timedelta(seconds=timeout_seconds)
        self.status_request = Request(command="_status", command_type="EPHEMERAL")

        super(PluginStatusMonitor, self).__init__(
            logger=self.logger, name="PluginStatusMonitor"
        )

    def run(self):
        self.logger.info(self.display_name + " is started")

        while not self.wait(self.heartbeat_interval):
            self.request_status()
            self.check_status()

        self.logger.info(self.display_name + " is stopped")

    def request_status(self):
        try:
            self.clients["pika"].publish_request(
                self.status_request,
                routing_key="admin",
                expiration=str(self.heartbeat_interval * 1000),
            )
        except Exception as ex:
            self.logger.warning("Unable to publish status request: %s", str(ex))

    def check_status(self):
        """Update instance status if necessary"""

        for instance in Instance.objects:
            if self.stopped():
                break

            last_heartbeat = instance.status_info["heartbeat"]

            if last_heartbeat:
                if (
                    instance.status == "RUNNING"
                    and datetime.utcnow() - last_heartbeat >= self.timeout
                ):
                    instance.status = "UNRESPONSIVE"
                    instance.save()
                elif (
                    instance.status
                    in ["UNRESPONSIVE", "STARTING", "INITIALIZING", "UNKNOWN"]
                    and datetime.utcnow() - last_heartbeat < self.timeout
                ):
                    instance.status = "RUNNING"
                    instance.save()
