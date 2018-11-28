import pytest
from mock import Mock

import bg_utils
from bg_utils.event_publisher import EventPublishers, EventPublisher
from brewtils.models import Event


@pytest.fixture
def event():
    return Event(name='mock', payload='Hello!')


class TestEventPublishers(object):

    @pytest.fixture
    def connection(self):
        return Mock()

    @pytest.fixture
    def publishers(self, connection):
        return EventPublishers(connections={'mock': connection})

    def test_publish_event(self, event, connection, publishers):
        publishers.publish_event(event)
        connection.publish_event.assert_called_once_with(event)

    def test_publish_event_metadata_funcs(self, event, connection, publishers):
        publishers.metadata_funcs = {'mock': lambda: 'Hello'}

        publishers.publish_event(event)
        connection.publish_event.assert_called_once_with(event)
        assert event.metadata['mock'] == 'Hello'

    def test_publish_event_exception(self, caplog, connection, publishers):
        connection.publish_event = Mock(side_effect=Exception)

        publishers.publish_event(Mock())
        assert 1 == len(caplog.records)
        assert 'ERROR' == caplog.records[0].levelname

    def test_shutdown(self, connection, publishers):
        publishers.shutdown()
        assert connection.shutdown.called is True

    def test_magic(self, connection, publishers):
        assert connection == publishers['mock']
        assert 1 == len(publishers)

        for name in publishers:
            assert 'mock' == name

        connection2 = Mock()
        publishers['mock2'] = connection2
        assert connection2 == publishers['mock2']
        assert 2 == len(publishers)

        del publishers['mock2']
        assert 1 == len(publishers)


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
        assert event == publisher._event_prepare(event)

    def test_event_serialize(self, monkeypatch, event, publisher):
        parser = Mock()
        monkeypatch.setattr(bg_utils.event_publisher, 'SchemaParser', parser)

        publisher._event_serialize(event)
        parser.serialize_event.assert_called_once_with(event)

    def test_event_publish_args(self, event, publisher):
        assert {} == publisher._event_publish_args(event)
