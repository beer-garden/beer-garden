import requests

from beer_garden.events.events_manager import EventProcessor

from brewtils.models import Namespace, PatchOperation
from brewtils.schema_parser import SchemaParser


class ParentHttpProcessor(EventProcessor):
    """
    This is an example stubbed out for how parent listeners could publish events.
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

        self.namespace = namespace
        self.callback = config.callback

        self.registered = False

    def process_next_message(self, event):
        """
        Sends POST request to endpoint with the Event info.
        :param event: The Event to be processed
        :return:
        """

        if not self.registered:
            self.register_with_parent()
        if self.registered:

            if event.name == "BARTENDER_STARTED":
                response = requests.patch(self.endpoint + "namespace/" + self.namespace,
                                          json=SchemaParser.serialize(
                                              PatchOperation(operation="running"),
                                              to_string=False)
                                          )
            elif event.name == "BARTENDER_STOPPED":
                response = requests.patch(self.endpoint + "namespace/" + self.namespace,
                                          json=SchemaParser.serialize(
                                              PatchOperation(operation="stopped"),
                                              to_string=False)
                                              )
            # else:
            #    requests.post(
            #        self.endpoint + "event", json=SchemaParser.serialize(event, to_string=False)
            #    )
        else:
            self.events_queue.put(event)



    def register_with_parent(self):

        try:
            response = requests.post(
                self.endpoint + "namespace/"+self.namespace,
                json=SchemaParser.serialize(Namespace(namespace=self.namespace,
                                                      status="INITIALIZING",
                                                      connection_type="https" if self.callback.ssl_enabled else "http",
                                                      connection_params=self.callback),
                                            to_string=False)
            )

            if response.status_code in ['200', '201']:
                self.registered = True
        except ConnectionError:
            self.registered = False

