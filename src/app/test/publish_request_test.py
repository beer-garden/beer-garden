

import pytest
from mock import Mock
from brewtils.models import Event, Events, Garden, System, Command, Request
import beer_garden

@pytest.fixture
def command_topic_one():
    return Command(
            name="command_one_topic", topics = ["topic_1"]
        )

@pytest.fixture
def command_topic_two():
    return Command(
            name="command_one_topic", topics = ["topic_2"]
        )

@pytest.fixture
def command_topic_one_and_two():
    return Command(
            name="command_one_topic", topics = ["topic_1","topic_2"]
        )

@pytest.fixture
def command_topic_any():
    return Command(
            name="command_one_topic", topics = ["topic.*"]
        )
    

@pytest.fixture
def localgarden_system(command_topic_one, command_topic_two, command_topic_one_and_two, command_topic_any):
    return System(
            name="localsystem", version="1.2.3", namespace="localgarden", local=True, instances=["default"],
            commands=[command_topic_one, command_topic_two, command_topic_one_and_two, command_topic_any]
        )
    


@pytest.fixture
def localgarden(localgarden_system):
    return Garden(
            name="localgarden", connection_type="LOCAL", systems=[localgarden_system]
        )


class TestSubscriptionEvent(object):
    def test_topic_one(self, monkeypatch, localgarden):

        mock_process_request = Mock(return_value=None)
        monkeypatch.setattr(beer_garden.publish_request, "process_request", mock_process_request)
        monkeypatch.setattr(beer_garden.publish_request, "get_gardens", Mock(return_value=[]))      
        monkeypatch.setattr(beer_garden.publish_request, "local_garden", Mock(return_value=localgarden))

        event = Event(name=Events.REQUEST_TOPIC_PUBLISH.name, metadata={"propagate": False, "topic":"topic_1"}, payload=Request())
        beer_garden.publish_request.process_publish_event(localgarden, event)

        assert mock_process_request.call_count == 3
