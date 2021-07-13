import time
from typing import Any, Dict

import pytest
import stomp
from brewtils.models import Operation
from brewtils.rest.easy_client import EasyClient
from brewtils.schema_parser import SchemaParser
from requests.models import Response
from stomp import StompConnection11
from stomp.listener import ConnectionListener


@pytest.fixture(scope="class")
def system_spec():
    return {
        "system": "echo",
        "system_version": "3.0.0.dev0",
        "instance_name": "default",
        "command": "say",
    }


class MessageListener(ConnectionListener):
    _create_event_captured: bool

    def __init__(self):
        super().__init__()
        self._create_event_captured = False

    def on_error(self, headers, message):
        print("received an error %s" % headers)

    def on_message(self, headers: Dict[str, Any], message: Any) -> None:
        """Set a property when a MESSAGE frame is received by the STOMP connection.

        If the needed key is in the headers dict and has the correct value, signal
        that we've been successful.

        Args:
            headers: a dictionary containing all headers sent by the server
            as key/value pairs.

            message: the frame's payload - the message body.
        """
        try:
            if "model_class" in headers:
                if headers["model_class"] == "Operation":
                    parsed = SchemaParser.parse_operation(message, from_string=True)

                    if parsed.model and parsed.model.name:
                        if parsed.model.name.startswith("REQUEST"):
                            self.create_event_captured = True
                        else:
                            print(f"ERROR: no 'REQUEST' is parsed model")
                    else:
                        print("ERROR: no parsed model found")
                elif headers["model_class"] == "error_message":
                    print(f"ERROR: Message returned: {message!r}")
                else:
                    print(f"ERROR: 'model_class' not in headers, message={message}")
        except Exception:
            print(f"ERROR: unable to parse, message={message}")

    @property
    def create_event_captured(self):
        return self._create_event_captured

    @create_event_captured.setter
    def create_event_captured(self, val: bool) -> None:
        self._create_event_captured = val


@pytest.mark.usefixtures("request_generator")
class TestPublisher(object):
    @staticmethod
    def create_stomp_connection() -> StompConnection11:
        """Create a Connection object with the correct parameters."""

        host_and_ports = [("localhost", 61613)]
        conn = stomp.Connection(host_and_ports=host_and_ports, heartbeats=(10000, 0))
        conn.connect(
            "beer_garden", "password", wait=True, headers={"client-id": "beer_garden"}
        )

        return conn

    def create_request(self, function: str) -> Dict[str, Any]:
        request_model = self.request_generator.generate_request(
            parameters={"message": "test_string", "loud": True}
        )

        request_model["metadata"] = {"generated-by": function}

        return request_model

    @pytest.mark.usefixtures("easy_client", "request_generator")
    def test_listen_create_request(self):
        """Publish a Request over HTTP and verify it from STOMP."""

        stomp_connection: StompConnection11 = self.create_stomp_connection()
        assert stomp_connection.is_connected()

        listener = MessageListener()
        stomp_connection.set_listener("bg_listener", listener)
        stomp_connection.subscribe(
            destination="Beer_Garden_Events",
            id="event_listener",
            ack="auto",
            headers={
                "subscription-type": "MULTICAST",
                "durable-subscription-name": "events",
            },
        )
        assert stomp_connection.get_listener("bg_listener") == listener
        assert stomp_connection.running

        request_easy_client: EasyClient = self.easy_client
        assert request_easy_client.can_connect()

        request_model: Dict[str, Any] = self.create_request(
            "test_listen_create_request"
        )
        sample_operation_request = Operation(
            operation_type="REQUEST_CREATE",
            model=request_model,
            model_type="Request",
        )

        forward_result: Response = request_easy_client.forward(sample_operation_request)
        assert forward_result.ok

        time.sleep(10)

        assert listener.create_event_captured

        if stomp_connection.is_connected():
            stomp_connection.disconnect()

    @pytest.mark.usefixtures("easy_client", "request_generator")
    def test_publish_create_request(self):
        """Publish a Request over STOMP and verify it via HTTP."""

        stomp_connection = self.create_stomp_connection()

        request_model = self.create_request("test_publish_create_request")

        sample_operation_request = Operation(
            operation_type="REQUEST_CREATE",
            model=request_model,
            model_type="Request",
            target_garden_name="docker",
        )

        listener = MessageListener()
        stomp_connection.set_listener("", listener)

        stomp_connection.subscribe(
            destination="Beer_Garden_Events",
            id="event_listener",
            ack="auto",
            headers={
                "subscription-type": "MULTICAST",
                "durable-subscription-name": "events",
            },
        )

        stomp_connection.send(
            body=SchemaParser.serialize_operation(
                sample_operation_request, to_string=True
            ),
            headers={
                "model_class": sample_operation_request.__class__.__name__,
            },
            destination="Beer_Garden_Operations",
        )

        time.sleep(10)

        requests = self.easy_client.find_requests()

        found_request = False

        print(len(requests))
        for request in requests:
            print(SchemaParser.serialize_request(request, to_string=True))
            if (
                "generated-by" in request.metadata
                and request.metadata["generated-by"] == "test_publish_create_request"
            ):
                found_request = True
                break

        assert found_request

        assert listener.create_event_captured

        if stomp_connection.is_connected():
            stomp_connection.disconnect()
