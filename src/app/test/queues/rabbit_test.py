import pytest
from mock import Mock
from pyrabbit2.http import HTTPError, NetworkError

import beer_garden.requests
from beer_garden.queue.rabbit import PyrabbitClient, get_routing_key, get_routing_keys


class TestGetRoutingKey(object):
    def test_basic(self):
        assert "system.1-0-0.instance" == get_routing_key("system", "1.0.0", "instance")

    @pytest.mark.parametrize(
        "args,expected",
        [
            (("system", "1.0.0", "instance"), "admin.system.1-0-0.instance"),
            ((None, None, None), "admin"),
        ],
    )
    def test_admin(self, args, expected):
        assert get_routing_key(*args, is_admin=True) == expected


class TestGetRoutingKeys(object):
    def test_basic(self):
        assert ["system", "system.1-0-0", "system.1-0-0.instance"] == get_routing_keys(
            "system", "1.0.0", "instance"
        )

    def test_admin(self):
        assert ["admin"] == get_routing_keys(is_admin=True)
        assert ["admin"] == get_routing_keys(is_admin=True)

    def test_admin_no_clone_id(self):
        assert [
            "admin",
            "admin.system",
            "admin.system.1-0-0",
            "admin.system.1-0-0.instance",
        ] == get_routing_keys("system", "1.0.0", "instance", is_admin=True)


def test_get_routing_keys_admin_clone_id():
    expected = [
        "admin",
        "admin.system",
        "admin.system.1-0-0",
        "admin.system.1-0-0.instance",
        "admin.system.1-0-0.instance.clone",
    ]
    assert expected == get_routing_keys(
        "system", "1.0.0", "instance", "clone", is_admin=True
    )


# class TestPikaClient(object):
#     @pytest.fixture
#     def publish_mock(self):
#         return Mock()
#
#     @pytest.fixture
#     def client(self, publish_mock):
#         the_client = PikaClient(
#             host="localhost", port=5672, user="user", password="password"
#         )
#         the_client.publish = publish_mock
#
#         return the_client
#
#     def test_publish_request(self, client, bg_request, publish_mock):
#         client.publish_request(bg_request, routing_key="queue_name")
#         publish_mock.assert_called_once_with(
#             ANY, headers={"request_id": bg_request.id}, routing_key="queue_name"
#         )
#
#     def test_publish_no_routing_key(self, client, bg_request, publish_mock):
#         client.publish_request(bg_request)
#         publish_mock.assert_called_once_with(
#             ANY,
#             headers={"request_id": bg_request.id},
#             routing_key="system.1-0-0.default",
#         )
#
#     def test_publish_expiration(self, client, bg_request, publish_mock):
#         client.publish_request(bg_request, expiration=10)
#         publish_mock.assert_called_once_with(
#             ANY,
#             headers={"request_id": bg_request.id},
#             routing_key="system.1-0-0.default",
#             expiration=10,
#         )


class TestPyrabbitClient(object):
    @pytest.fixture
    def pyrabbit_client(self):
        return Mock()

    @pytest.fixture
    def client(self, pyrabbit_client):
        the_client = PyrabbitClient(
            host="localhost",
            port=15672,
            user="user",
            password="password",
            admin_expires=3600000,
        )
        the_client._client = pyrabbit_client

        return the_client

    def test_is_alive(self, client, pyrabbit_client):
        pyrabbit_client.is_alive.return_value = True
        assert client.is_alive() is True

    def test_not_alive(self, client, pyrabbit_client):
        pyrabbit_client.is_alive.side_effect = NetworkError
        assert client.is_alive() is False

    def test_verify_virtual_host(self, client, pyrabbit_client):
        virtual_host_mock = Mock()
        pyrabbit_client.get_vhost.return_value = virtual_host_mock

        assert client.verify_virtual_host() == virtual_host_mock
        pyrabbit_client.get_vhost.assert_called_once_with("/")

    def test_verify_virtual_host_exception(self, client, pyrabbit_client):
        pyrabbit_client.get_vhost.side_effect = ValueError

        with pytest.raises(ValueError):
            client.verify_virtual_host()
        pyrabbit_client.get_vhost.assert_called_once_with("/")

    def test_ensure_admin_expiry(self, client, pyrabbit_client):
        client.ensure_admin_expiry()
        assert pyrabbit_client.create_policy.called is True

    def test_ensure_admin_expiry_exception(self, client, pyrabbit_client):
        pyrabbit_client.create_policy.side_effect = ValueError
        with pytest.raises(ValueError):
            client.ensure_admin_expiry()

    def test_get_queue_size_good(self, client, pyrabbit_client):
        pyrabbit_client.get_queue.return_value = {"messages": 1}

        assert client.get_queue_size("queue") == 1
        pyrabbit_client.get_queue.assert_called_with("/", "queue")

    def test_get_queue_idle(self, client, pyrabbit_client):
        pyrabbit_client.get_queue.return_value = {}

        assert client.get_queue_size("queue") == 0
        pyrabbit_client.get_queue.assert_called_with("/", "queue")

    def test_get_queue_size_no_queue(self, client, pyrabbit_client):
        pyrabbit_client.get_queue.side_effect = HTTPError(
            {}, status=404, reason="something"
        )
        with pytest.raises(HTTPError):
            client.get_queue_size("queue")

    def test_get_queue_size_bad_exception(self, client, pyrabbit_client):
        pyrabbit_client.get_queue.side_effect = HTTPError(
            {}, status=500, reason="something"
        )
        with pytest.raises(HTTPError):
            client.get_queue_size("queue")

    def test_clear_queue_no_messages(self, client, pyrabbit_client):
        pyrabbit_client.get_queue.return_value = {"messages_ready": 0}

        client.clear_queue("queue")
        assert pyrabbit_client.get_queue.called is True
        assert pyrabbit_client.get_messages.called is False

    def test_clear_queue_idle_queue(self, client, pyrabbit_client):
        pyrabbit_client.get_queue.return_value = {}

        client.clear_queue("queue")
        assert pyrabbit_client.get_queue.called is True
        assert pyrabbit_client.get_messages.called is False

    def test_clear_queue(self, monkeypatch, client, pyrabbit_client):
        fake_request = Mock(id="id", status="CREATED")
        pyrabbit_client.get_queue.return_value = {"messages_ready": 1}
        pyrabbit_client.get_messages.return_value = [{"payload": fake_request}]

        parser_mock = Mock(parse_request=Mock(return_value=fake_request))
        monkeypatch.setattr("beer_garden.queue.rabbit.SchemaParser", parser_mock)

        cancel_mock = Mock()
        monkeypatch.setattr(beer_garden.requests, "cancel_request", cancel_mock)

        client.clear_queue("queue")
        cancel_mock.assert_called_once_with(fake_request.id)

    def test_clear_queue_bad_payload(self, monkeypatch, client, pyrabbit_client):
        fake_request = Mock(id="id", status="CREATED")
        pyrabbit_client.get_queue.return_value = {"messages_ready": 1}
        pyrabbit_client.get_messages.return_value = [{"payload": fake_request}]

        parser_mock = Mock(parse_request=Mock(side_effect=ValueError))
        monkeypatch.setattr("beer_garden.queue.rabbit.SchemaParser", parser_mock)

        client.clear_queue("queue")
        assert fake_request.status == "CREATED"
        assert fake_request.save.called is False
        assert pyrabbit_client.get_messages.called is True
        pyrabbit_client.get_messages.assert_called_with(
            "/", "queue", count=1, requeue=False
        )
        parser_mock.parse_request.assert_called_once_with(
            fake_request, from_string=True
        )

    def test_clear_queue_race_condition(self, monkeypatch, client, pyrabbit_client):
        pyrabbit_client.get_queue.return_value = {"messages_ready": 1}
        pyrabbit_client.get_messages.return_value = []

        parser_mock = Mock()
        monkeypatch.setattr("beer_garden.queue.rabbit.SchemaParser", parser_mock)

        client.clear_queue("queue")
        assert pyrabbit_client.get_messages.called is True
        assert parser_mock.parse_request.called is False

    def test_delete_queue(self, client, pyrabbit_client):
        client.delete_queue("queue")
        assert pyrabbit_client.delete_queue.called is True

    def test_destroy_queue_all_exceptions(self, client):
        disconnect_consumers_mock = Mock(side_effect=ValueError)
        clear_queue_mock = Mock(side_effect=ValueError)
        delete_queue = Mock(side_effect=ValueError)
        client.disconnect_consumers = disconnect_consumers_mock
        client.clear_queue = clear_queue_mock
        client.delete_queue = delete_queue

        client.destroy_queue("queue_name", True)
        assert disconnect_consumers_mock.called is True
        assert clear_queue_mock.called is True
        assert delete_queue.called is True

    def test_destroy_queue_with_http_errors(self, client):
        disconnect_consumers_mock = Mock(side_effect=HTTPError({}, status=500))
        clear_queue_mock = Mock(side_effect=HTTPError({}, status=500))
        delete_queue = Mock(side_effect=HTTPError({}, status=500))
        client.disconnect_consumers = disconnect_consumers_mock
        client.clear_queue = clear_queue_mock
        client.delete_queue = delete_queue

        client.destroy_queue("queue_name", True)
        assert disconnect_consumers_mock.called is True
        assert clear_queue_mock.called is True
        assert delete_queue.called is True

    def test_destroy_queue_no_errors(self, client):
        disconnect_consumers_mock = Mock()
        clear_queue_mock = Mock()
        delete_queue = Mock()
        client.disconnect_consumers = disconnect_consumers_mock
        client.clear_queue = clear_queue_mock
        client.delete_queue = delete_queue

        client.destroy_queue("queue_name", True)
        assert disconnect_consumers_mock.called is True
        assert clear_queue_mock.called is True
        assert delete_queue.called is True

    def test_destroy_queue_none_queue_name(self, client, pyrabbit_client):
        disconnect_consumers_mock = Mock()
        clear_queue_mock = Mock()
        delete_queue = Mock()
        client.disconnect_consumers = disconnect_consumers_mock
        client.clear_queue = clear_queue_mock
        client.delete_queue = delete_queue

        client.destroy_queue(None)
        assert disconnect_consumers_mock.called is False
        assert clear_queue_mock.called is False
        assert delete_queue.called is False

    def test_disconnect_consumers(self, client, pyrabbit_client):
        consumer_details = [
            {
                "queue": {"name": "queue_name"},
                "channel_details": {"connection_name": "conn"},
            }
        ]
        pyrabbit_client.get_channels.return_value = [{"name": "channel_name"}]
        pyrabbit_client.get_channel.return_value = {
            "consumer_details": consumer_details
        }

        client.disconnect_consumers("queue_name")
        pyrabbit_client.delete_connection.assert_called_once_with("conn")

    def test_disconnect_consumers_no_channels(self, client, pyrabbit_client):
        pyrabbit_client.get_channels.return_value = None

        client.disconnect_consumers("queue_name")
        assert pyrabbit_client.delete_connection.called is False

    def test_disconnect_consumers_no_channel(self, client, pyrabbit_client):
        channel = {"name": "channel_name"}
        pyrabbit_client.get_channels.return_value = [channel]
        pyrabbit_client.get_channel.return_value = None

        client.disconnect_consumers("queue_name")
        assert pyrabbit_client.delete_connection.called is False
