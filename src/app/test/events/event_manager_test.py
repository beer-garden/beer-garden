import pytest
from mock import Mock
from beer_garden.events.events_manager import EventsManager, EventProcessor
from multiprocessing import Queue
from brewtils.models import Event


class TestEventManager(object):
    @pytest.fixture
    def event(self):
        return Event(name="mock", payload="Hello!")

    @pytest.fixture
    def event_processor(self):
        return EventProcessor()

    @pytest.fixture
    def event_manager(self):
        return EventsManager(Queue())

    def test_add_event(self, event, events_manager):
        events_manager.add_event(event)

        assert events_manager.events_queue.get() == event

    def test_register_listener(self, event_processor, event_manager):
        event_manager.register_processor(event_processor)

        assert len(event_manager.event_processors) == 1
