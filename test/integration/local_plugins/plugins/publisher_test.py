import pytest
import time

from brewtils.models import Topic, Subscriber


@pytest.fixture(scope="class")
def system_spec():
    return {
        "system": "publisher",
        "system_version": "3.0.0.dev0",
        "instance_name": "default",
        "command": "publish_topics",
    }


@pytest.fixture
def topic1():
    return Topic(
        name="newtopic",
        subscribers=[
            Subscriber(
                garden=None,
                namespace=None,
                system="subscribe",
                instance=None,
                version=None,
                command="subscribe_wildcard_topics",
            )
        ],
    )


@pytest.fixture
def topic():
    return Topic(
        name="topic",
        subscribers=[
            Subscriber(
                garden=None,
                namespace=None,
                system="subscribe",
                instance=None,
                version=None,
                command="subscribe_wildcard_topics",
            )
        ],
    )


@pytest.mark.usefixtures("easy_client", "request_generator")
class TestPublish(object):

    def wait_for_request(self, request, expected_length):
        check = 0
        while check < 12:
            completed_request = self.easy_client.find_unique_request(id=request.id)
            if len(completed_request.children) == expected_length:
                return completed_request
            time.sleep(15)
            check += 1

        return request

    def test_one_trigger_topic_subscriber(self, topic1):
        newtopic = self.easy_client.create_topic(topic1)
        request_dict = self.request_generator.generate_request(
            parameters={"topic": "newtopic", "value": "test"}
        )
        request = self.easy_client.create_request(request_dict)

        completed_request = self.wait_for_request(request, 1)

        for child_request in completed_request.children:
            assert child_request.command == "subscribe_wildcard_topics"

        assert len(completed_request.children) == 1
        self.easy_client.remove_topic(newtopic.id)

    def test_one_trigger_topic_command_and_subscriber(self, topic):
        topic = self.easy_client.create_topic(topic)
        request_dict = self.request_generator.generate_request(
            parameters={"topic": "topic", "value": "test"}
        )
        request = self.easy_client.create_request(request_dict)

        completed_request = self.wait_for_request(request, 1)

        for child_request in completed_request.children:
            assert child_request.command == "subscribe_wildcard_topics"

        assert len(completed_request.children) == 1
        self.easy_client.remove_topic(topic.id)

    def test_one_trigger(self):
        request_dict = self.request_generator.generate_request(
            parameters={"topic": "topic", "value": "test"}
        )
        request = self.easy_client.create_request(request_dict)

        completed_request = self.wait_for_request(request, 1)

        for child_request in completed_request.children:
            assert child_request.command == "subscribe_wildcard_topics"

        assert len(completed_request.children) == 1

    def test_two_trigger(self):
        request_dict = self.request_generator.generate_request(
            parameters={"topic": "topic2", "value": "test"}
        )
        request = self.easy_client.create_request(request_dict)

        completed_request = self.wait_for_request(request, 2)

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

        completed_request = self.wait_for_request(request, 3)

        for child_request in completed_request.children:
            assert child_request.command in [
                "subscribe_wildcard_topics",
                "subscribe_multiple_topics",
                "subscrib_one_topics",
            ]

        assert len(completed_request.children) == 3
