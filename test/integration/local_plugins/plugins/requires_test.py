import time

import pytest
from brewtils.rest.easy_client import EasyClient


# @pytest.mark.usefixtures("easy_client")
class TestRequestLogic(object):

    COMPLETED_STATUSES = ["SUCCESS", "ERROR", "CANCELED"]

    def check_status(self, client, system_name, status, timeout=1, max_delay=1):
        system = client.find_unique_system(name=system_name)
        assert len(system.instances) > 0

        matched = False
        for instance in system.instances:
            matched = instance.status == status

        delay_time = 0.01
        total_wait_time = 0
        while not matched:
            if timeout and total_wait_time > timeout:
                raise TimeoutError("Timed out waiting for request to complete")

            time.sleep(delay_time)
            total_wait_time += delay_time
            delay_time = min(delay_time * 2, max_delay)
            system = client.find_unique_system(name=system_name)
            for instance in system.instances:
                matched = instance.status == status

    def stop_system(self, client, system_name):

        system = client.find_unique_system(name=system_name)
        assert system.name == system_name
        assert len(system.instances) == 1

        for instance in system.instances:
            client.client.patch_instance(instance.id, '{"operation":"stop"}')

        self.check_status(client, system_name, "STOPPED", timeout=10)

    def start_system(self, client, system_name):
        system = client.find_unique_system(name=system_name)

        for instance in system.instances:
            client.client.patch_instance(instance.id, '{"operation":"start"}')

        self.check_status(client, system_name, "RUNNING", timeout=10)

    def run_request(self, client, execution_number):
        request = {
            "system": "echo-sleeper",
            "system_version": "3.0.0.dev0",
            "command": "say_error_and_catch",
            "instance_name": "default",
            "comment": f"Execution {execution_number}",
            "parameters": {"message": "test_string", "loud": True},
        }

        request = client.create_request(request)

        return request

    def wait_for_response(self, client, request, timeout=1, max_delay=1):
        delay_time = 0.01
        total_wait_time = 0
        while request.status not in self.COMPLETED_STATUSES:
            if timeout and total_wait_time > timeout:
                raise TimeoutError("Timed out waiting for request to complete")

            time.sleep(delay_time)
            total_wait_time += delay_time
            delay_time = min(delay_time * 2, max_delay)

            request = client.find_unique_request(id=request.id)

        return request

    def test_requires_sleeper_echo(self):

        for execution_number in range(20):
            easy_client = EasyClient(
                bg_host="localhost", bg_port=2337, ssl_enabled=False
            )
            assert easy_client.can_connect()

            self.stop_system(easy_client, "sleeper")
            self.stop_system(easy_client, "echo")

            self.check_status(
                easy_client, "echo-sleeper", "AWAITING_SYSTEM", timeout=60
            )

            request = self.run_request(easy_client, execution_number)
            self.start_system(easy_client, "echo")

            with pytest.raises(TimeoutError):
                updated_request = self.wait_for_response(
                    easy_client, request, timeout=60
                )
            self.start_system(easy_client, "sleeper")

            updated_request = self.wait_for_response(easy_client, request, timeout=120)

            assert updated_request.status == "SUCCESS"
