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

    @pytest.mark.usefixtures('easy_client')
    def test_publish_create_request(self, stomp_connection):
        """Published the Request over STOMP and verifies of HTTP"""

        request_model = Request(
            system="echo",
            system_version="1.0.0.dev0",
            instance_name="default",
            command="say",
            parameters={"message": "Hello, World!", "loud": True},
            namespace="default",
            metadata={"generated-by": "test_publish_create_request"},
        )

        sample_operation_request = Operation(
            operation_type="REQUEST_CREATE",
            model=request_model,
            model_type="Request",
        )

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

        for request in requests:
            if "generated-by" in request.metadata and request.metadata["generated-by"] == "test_publish_create_request":
                found_request = True
                break

        assert found_request


