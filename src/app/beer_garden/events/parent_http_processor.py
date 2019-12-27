import requests

from beer_garden.events.events_manager import EventProcessor

from brewtils.models import Namespace, PatchOperation
from brewtils.schema_parser import SchemaParser


class ParentHttpProcessor(EventProcessor):
    """
    Forwards events to parent Beer Garden instance.
    """

    def __init__(self, config, namespace):
        """

        :param config:
        """
        super().__init__()
        self.endpoint = "{}://{}:{}{}api/v1/".format(
            "https" if config.ssl.enabled else "http",
            config.public_fqdn,
            config.port,
            config.url_prefix,
        )

        self.skip_events = config.skip_events

        self.namespace = namespace
        self.callback = config.callback

        self.registered = False
        self.wait_time = 0.1
        self.connected = False

        self._register_with_parent()

    def process_next_message(self, event):
        """
        Sends POST request to endpoint with the Event info.
        :param event: The Event to be processed
        :return:
        """

        if event.name in self.skip_events:
            return

        response = None
        if not self.connected:

            if event.name == Events.BARTENDER_STOPPED.name:
                self.clear_queue()
            else:
                self._register_with_parent()

        if self.connected:
            try:
                if event.name == Events.BARTENDER_STARTED.name:
                    response = self._patch(
                        "namespaces/",
                        self.namespace,
                        [PatchOperation(operation="running")],
                    )
                elif event.name == Events.BARTENDER_STOPPED.name:
                    response = self._patch(
                        "namespaces/",
                        self.namespace,
                        [PatchOperation(operation="stopped")],
                    )
                    self.clear_queue()
                elif event.name == Events.REQUEST_CREATED.name:
                    response = self._post("requests/", event.payload)
                elif event.name in (
                    Events.REQUEST_STARTED.name,
                    Events.REQUEST_UPDATED.name,
                    Events.REQUEST_COMPLETED.name,
                ):
                    response = self._patch(
                        "requests/", event.payload.id, event.metadata
                    )

                    # Try to create the Request if it didn't exist
                    if response.status_code == 500:
                        response = self._post("requests/", event.payload)

                elif event.name == Events.SYSTEM_CREATED.name:
                    response = self._post("systems/", event.payload)
                elif event.name == Events.SYSTEM_UPDATED.name:
                    responses = self._patch(
                        "systems/", event.payload.id, event.metadata
                    )

                    # Try to create the System if it didn't exist
                    if response.status_code == 500:
                        response = self._post("systems/", event.payload)
                elif event.name == Events.SYSTEM_REMOVED.name:
                    response == self._delete("systems/", event.payload.id)

                elif event.name in (
                    Events.INSTANCE_INITIALIZED.name,
                    Events.INSTANCE_STARTED.name,
                    Events.INSTANCE_UPDATED.name,
                    Events.INSTANCE_STOPPED.name,
                ):
                    responses = self._patch(
                        "instances/", event.payload.id, event.metadata
                    )

                    if responses[0].status_code == 500:
                        self._build_system_from_instance(event)

                elif event.name == Events.NAMESPACE_CREATED.name:
                    pass
                elif event.name == Events.NAMESPACE_UPDATED.name:
                    pass
                elif event.name == Events.NAMESPACE_REMOVED.name:
                    pass
                elif event.name == Events.ALL_QUEUES_CLEARED.name:
                    pass
                elif event.name == Events.QUEUE_CLEARED.name:
                    pass
            except requests.exceptions.ConnectionError:
                self.logger.warning(
                    "Lost connect with Parent Endpoint: " + self.endpoint
                )
                self.connected = False
                self.wait_time = 0.1
                self.events_queue.put(event)

        else:
            self.events_queue.put(event)

    def _post(self, endpoint, payload):
        return requests.post(
            self.endpoint + endpoint, json=SchemaParser.serialize(payload)
        )

    def _patch(self, endpoint, uuid, metadata):
        responses = list()
        for data in metadata:
            responses.append(
                requests.patch(
                    self.endpoint + endpoint + uuid,
                    json=SchemaParser.serialize_patch(data, to_string=False),
                )
            )
        return responses

    def _delete(self, endpoint, uuid):
        return requests.delete(self.endpoint + endpoint + uuid)

    def _build_system_from_instance(self, event):
        # Need to query DB for System Object
        system = db.query_unique(System, instances__contains=event.payload)
        return self._post("systems/", system)

    def _register_with_parent(self):

        try:
            if not self.registered:
                response = requests.post(
                    self.endpoint + "namespaces/" + self.namespace,
                    json=SchemaParser.serialize(
                        Namespace(
                            namespace=self.namespace,
                            status="INITIALIZING",
                            connection_type="https"
                            if self.callback.ssl_enabled
                            else "http",
                            connection_params=self.callback,
                        ),
                        to_string=False,
                    ),
                )
                if response.status_code in [200, 201]:
                    self.registered = True
                    self.connected = True
            else:
                response = self._patch(
                    "namespaces/", self.namespace, [PatchOperation(operation="running")]
                )
                if response[0].status_code in [200, 201]:
                    self.connected = True

        except requests.exceptions.ConnectionError as ce:
            self.connected = False
            self.wait_time = min(self.wait_time * 2, 30)
            self.logger.warning(
                "Waiting %.1f seconds before next attempt to register with Parent",
                self.wait_time,
            )
            self.wait(self.wait_time)
