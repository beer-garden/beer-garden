import pytest
from mock import Mock

import beer_garden.bg_utils
from beer_garden.bg_utils.event_publisher import EventPublishers, EventPublisher
from brewtils.models import Event


@pytest.fixture
def event():
    return Event(name="mock", payload="Hello!")


class TestEventPublishers(object):
    @pytest.fixture
    def connection(self):
        return Mock()

    @pytest.fixture
    def publishers(self, connection):
        return EventPublishers(connections={"mock": connection})

    def test_publish_event(self, event, connection, publishers):
        publishers.publish_event(event)
        connection.publish_event.assert_called_once_with(event)

    def test_publish_event_metadata_funcs(self, event, connection, publishers):
        publishers.metadata_funcs = {"mock": lambda: "Hello"}

        publishers.publish_event(event)
        connection.publish_event.assert_called_once_with(event)
        assert event.metadata["mock"] == "Hello"

    def test_publish_event_exception(self, caplog, connection, publishers):
        connection.publish_event.side_effect = ValueError("Oops!")

        publishers.publish_event(Mock())
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"

    def test_shutdown(self, connection, publishers):
        publishers.shutdown()
        assert connection.shutdown.called is True

    def test_magic(self, connection, publishers):
        assert publishers["mock"] == connection
        assert len(publishers) == 1

        for name in publishers:
            assert name == "mock"

        connection2 = Mock()
        publishers["mock2"] = connection2
        assert publishers["mock2"] == connection2
        assert len(publishers) == 2

        del publishers["mock2"]
        assert len(publishers) == 1


class TestEventPublisher(object):
    @pytest.fixture
    def publisher(self):
        return EventPublisher()

    def test_publish_event(self, event, publisher):
        publish_mock = Mock()
        publisher.publish = publish_mock

        publisher.publish_event(event)
        assert publish_mock.called is True

    def test_event_prepare(self, event, publisher):
        assert publisher._event_prepare(event) == event

    def test_event_serialize(self, monkeypatch, event, publisher):
        parser = Mock()
        monkeypatch.setattr(
            beer_garden.bg_utils.event_publisher, "SchemaParser", parser
        )

        publisher._event_serialize(event)
        parser.serialize_event.assert_called_once_with(event)

    def test_event_publish_args(self, event, publisher):
        assert publisher._event_publish_args(event) == {}
