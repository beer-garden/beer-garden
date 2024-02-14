import pytest
import time


@pytest.fixture(scope="class")
def system_spec():
    return {
        "system": "publisher",
        "system_version": "3.0.0.dev0",
        "instance_name": "default",
        "command": "publish_topics",
    }


@pytest.mark.usefixtures("easy_client", "request_generator")
class TestPublish(object):
    def test_one_trigger(self):
        request_dict = self.request_generator.generate_request(
            parameters={"topic": "topic", "value": "test"}
        )
        request = self.easy_client.create_request(request_dict)

        time.sleep(30)
        completed_request = self.easy_client.find_unique_request(id=request.id)

        for child_request in completed_request.children:
            assert child_request.command == "subscribe_wildcard_topics"

        assert len(completed_request.children) == 1

    def test_two_trigger(self):
        request_dict = self.request_generator.generate_request(
            parameters={"topic": "topic2", "value": "test"}
        )
        request = self.easy_client.create_request(request_dict)

        time.sleep(30)
        completed_request = self.easy_client.find_unique_request(id=request.id)

        for child_request in completed_request.children:
            assert child_request.command in [
                "subscribe_wildcard_topics",
                "subscribe_multiple_topics",
            ]

        assert len(completed_request.children) == 2

    def test_three_trigger(self):
        request_dict = self.request_generator.generate_request(
            parameters={"topic": "topic1", "value": "test"}
        )
        request = self.easy_client.create_request(request_dict)

        time.sleep(30)
        completed_request = self.easy_client.find_unique_request(id=request.id)

        for child_request in completed_request.children:
            assert child_request.command in [
                "subscribe_wildcard_topics",
                "subscribe_multiple_topics",
                "subscrib_one_topics",
            ]

        assert len(completed_request.children) == 3
