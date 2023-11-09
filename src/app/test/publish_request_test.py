

import pytest
from mock import Mock
from brewtils.models import Event, Events, Garden, System, Command, Request
import beer_garden.publish_request


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
            name="localsystem", version="1.2.3", namespace="localgarden", local=True,
            commands=[command_topic_one, command_topic_two, command_topic_one_and_two, command_topic_any]
        )
    


@pytest.fixture
def localgarden(localgarden_system):
    return Garden(
            name="localgarden", connection_type="LOCAL", systems=[localgarden_system]
        )

@pytest.fixture
def mock_process_request(monkeypatch):
    find_mock = Mock()
    monkeypatch.setattr(beer_garden.requests, "process_request", find_mock)
    return find_mock

@pytest.fixture
def mock_get_gardens(monkeypatch):

    Garden(systems = [])

    find_mock = Mock(return_value=[])
    monkeypatch.setattr(beer_garden.garden, "get_gardens", find_mock)
    return find_mock

@pytest.fixture
def mock_local_garden(monkeypatch, localgarden):
    find_mock = Mock(return_value=localgarden)
    monkeypatch.setattr(beer_garden.garden, "local_garden", find_mock)
    return find_mock

class TestSubscriptionEvent(object):
    def test_topic_one(self, mock_local_garden, mock_process_request):


        event = Event(name=Events.REQUEST_TOPIC_PUBLISH.name, metadata={"propagate": False, "topic":"topic_1"}, payload=Request())
        beer_garden.publish_request.handle_event(event)

        assert mock_process_request.call_count == 3
