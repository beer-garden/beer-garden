import signal

import stomp
from brewtils.models import Operation, Request
from brewtils.schema_parser import SchemaParser
import pytest
import time

from brewtils.errors import ValidationError

try:
    from helper import delete_plugins
    from helper.assertion import assert_system_running
    from helper.plugin import (create_plugin, start_plugin, stop_plugin,
                               TestPluginV1, TestPluginV2,
                               TestPluginV1BetterDescriptions)
except:
    from ...helper import delete_plugins
    from ...helper.assertion import assert_system_running
    from ...helper.plugin import (create_plugin, start_plugin, stop_plugin,
                                  TestPluginV1, TestPluginV2,
                                  TestPluginV1BetterDescriptions)

@pytest.fixture(scope="class")
def system_spec():
    return {'system': 'echo', 'system_version': '3.0.0.dev0', 'instance_name': 'default',
            'command': 'say'}

class MessageListener(object):
    create_event_captured = False

    def on_error(self, headers, message):
        print('received an error %s' % headers)

    def on_message(self, headers, message):
        print(message)
        print(headers)
        # try:
        #     parsed = SchemaParser.parse(message, from_string=True, model_class=eval(headers['model_class']))
        #     print("Parsed message:", parsed)
        #
        #     if isinstance(parsed, Operation):
        #         if parsed.payload and parsed.payload.payload_type and parsed.payload.payload_type == "REQUEST_CREATED":
        #             self.create_event_captured = True
        # except:
        #     print("Error: unable to parse message:", message)


class TestPublisher(object):

    @pytest.fixture()
    def stomp_connection(self):
        """Creates the Connection class and closes when completed"""

        host_and_ports = [("localhost", 61613)]
        conn = stomp.Connection(host_and_ports=host_and_ports, heartbeats=(10000, 0))

        conn.connect(
            "beer_garden", "password", wait=True, headers={"client-id": "beer_garden"}
        )

        yield conn

        if conn.is_connected():
            conn.disconnect()

    @pytest.mark.usefixtures('easy_client', 'request_generator')
    def test_publish_create_request(self, stomp_connection):
        """Published the Request over STOMP and verifies of HTTP"""

        # request_model = Request(
        #     system="echo",
        #     system_version="3.0.0.dev0",
        #     instance_name="default",
        #     command="say",
        #     parameters={"message": "Hello, World!", "loud": True},
        #     namespace="docker",
        #     metadata={"generated-by": "test_publish_create_request"},
        # )

        request_model = self.request_generator.generate_request(parameters={"message": "test_string", "loud": True})

        request_model['metadata'] = {"generated-by": "test_publish_create_request"}

        sample_operation_request = Operation(
            operation_type="REQUEST_CREATE",
            model=request_model,
            model_type="Request",
        )

        stomp_connection.set_listener('', MessageListener())

        # stomp_connection.subscribe(destination='Beer_Garden_Operations', id='operation_listener', ack='auto',
        #                            headers={'subscription-type': 'MULTICAST', 'durable-subscription-name': 'Beer_Garden_Operations'})

        stomp_connection.subscribe(destination='Beer_Garden_Events', id='event_listener', ack='auto',
                                   headers={'subscription-type': 'MULTICAST',
                                            'durable-subscription-name': 'events'})

        stomp_connection.send(
            body=SchemaParser.serialize_operation(sample_operation_request, to_string=True),
            headers={
                "model_class": sample_operation_request.__class__.__name__,
            },
            destination="Beer_Garden_Operations",
        )

        time.sleep(10)

        requests = self.easy_client.find_requests()

        found_request = False

        #print(len(requests))

        for request in requests:
            #print(request.metadata)
            if "generated-by" in request.metadata and request.metadata["generated-by"] == "test_publish_create_request":
                found_request = True
                break

        assert found_request
