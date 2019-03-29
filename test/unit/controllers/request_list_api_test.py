import json

import pytest
from mock import MagicMock, Mock, PropertyMock, patch
from tornado.gen import Future
from tornado.httpclient import HTTPRequest

import bg_utils
import brew_view
from bg_utils.mongo.models import System
from brew_view.controllers import RequestListAPI
from brewtils.rest.client import RestClient
from brewtils.schema_parser import SchemaParser
from . import TestHandlerBase


@pytest.fixture(autouse=True)
def setup_systems(app, mongo_system):
    System.drop_collection()
    mongo_system.deep_save()


@pytest.fixture(autouse=True)
def thrift(monkeypatch, thrift_context, thrift_client, process_future):
    thrift_client.processRequest.return_value = process_future
    monkeypatch.setattr(
        brew_view.controllers.request_list_api, "thrift_context", thrift_context
    )


@pytest.fixture(autouse=True)
def latency_total(monkeypatch):
    latency_total = Mock()
    monkeypatch.setattr(
        brew_view.controllers.request_list_api, "http_api_latency_total", latency_total
    )
    return latency_total


@pytest.fixture
def process_future():
    return Future()


@pytest.fixture
def post_request(base_url, bg_request):
    bg_request.parent = None
    return HTTPRequest(
        base_url + "/api/v1/requests/",
        method="POST",
        headers=RestClient.JSON_HEADERS,
        body=SchemaParser.serialize_request(bg_request, to_string=True),
    )


class TestBlocking(object):
    """Test blocking functionality

    Testing the metrics and event publishing is kind of tricky. For these tests the
    request goes through the entire handler chain (aka BaseHander.on_finish is called).
    Since the difference there is WHEN in the process those things happen it makes it
    difficult.

    So we mock out the metrics call in the actual request list module and use that to
    determine if it was called in the 'correct' place.

    Because of the implementation of the event publishers we can't do the same thing
    there. So just check to ensure that the publish was called.

    """

    @pytest.mark.gen_test
    def test_no_blocking(
        self, app, process_future, http_client, latency_total, post_request
    ):
        process_future.set_result(None)

        response = yield http_client.fetch(post_request)
        assert response.code == 201
        assert latency_total.labels.return_value.observe.called is False
        assert brew_view.event_publishers["mock"].publish_event.called is True
        assert len(brew_view.request_map) == 0

    @pytest.mark.gen_test
    def test_blocking(
        self,
        app,
        process_future,
        io_loop,
        http_client,
        latency_total,
        post_request,
        bg_request,
    ):
        process_future.set_result(None)
        io_loop.call_later(0.25, lambda: brew_view.request_map[bg_request.id].set())

        post_request.url += "?blocking=true"
        response = yield http_client.fetch(post_request)

        assert response.code == 201
        assert latency_total.labels.return_value.observe.called is True
        assert brew_view.event_publishers["mock"].publish_event.called is True
        assert len(brew_view.request_map) == 0

    @pytest.mark.gen_test
    def test_blocking_timeout(
        self,
        app,
        process_future,
        io_loop,
        http_client,
        latency_total,
        post_request,
        bg_request,
    ):
        process_future.set_result(None)
        io_loop.call_later(0.25, lambda: brew_view.request_map[bg_request.id].set())

        post_request.url += "?blocking=true&timeout=0"
        response = yield http_client.fetch(post_request, raise_error=False)

        assert response.code == 408
        assert latency_total.labels.return_value.observe.called is True
        assert brew_view.event_publishers["mock"].publish_event.called is True
        assert len(brew_view.request_map) == 0


class RequestListAPITest(TestHandlerBase):
    def setUp(self):
        self.request_mock = MagicMock(name="Request Mock")
        self.request_mock.only.return_value = self.request_mock
        self.request_mock.search_text.return_value = self.request_mock
        self.request_mock.order_by.return_value = self.request_mock
        self.request_mock.id = "id"
        self.request_mock.instance_name = "default"
        self.request_mock.__getitem__.return_value = self.request_mock
        self.request_mock.__len__.return_value = 1

        mongo_patcher = patch("brew_view.controllers.request_list_api.Request.objects")
        self.addCleanup(mongo_patcher.stop)
        self.mongo_mock = mongo_patcher.start()
        self.mongo_mock.count.return_value = 1

        serialize_patcher = patch(
            "brew_view.controllers.request_list_api.MongoParser.serialize_request"
        )
        self.addCleanup(serialize_patcher.stop)
        self.serialize_mock = serialize_patcher.start()
        self.serialize_mock.return_value = "serialized_request"

        self.client_mock = Mock(name="client_mock")
        self.fake_context = MagicMock(
            __enter__=Mock(return_value=self.client_mock),
            __exit__=Mock(return_value=False),
        )
        self.future_mock = Future()

        super(RequestListAPITest, self).setUp()

    @patch("brew_view.controllers.request_list_api.RequestListAPI._get_query_set")
    def test_get(self, get_query_set_mock):
        query_set = MagicMock()
        query_set.count.return_value = 1
        query_set.__getitem__ = lambda *_: ["request"]
        get_query_set_mock.return_value = (query_set, None)

        response = self.fetch("/api/v1/requests?draw=1")
        self.assertEqual(200, response.code)
        self.serialize_mock.assert_called_once_with(
            ["request"], many=True, only=None, to_string=True
        )
        self.assertEqual("0", response.headers["start"])
        self.assertEqual("1", response.headers["length"])
        self.assertEqual("1", response.headers["recordsFiltered"])
        self.assertEqual("1", response.headers["recordsTotal"])
        self.assertEqual("1", response.headers["draw"])

    @patch("brew_view.controllers.request_list_api.System.objects")
    @patch("brew_view.controllers.request_list_api.MongoParser.parse_request")
    @patch("brew_view.controllers.request_list_api.thrift_context")
    def test_post_json(self, context_mock, parse_mock, system_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.processRequest.return_value = self.future_mock
        self.future_mock.set_result(None)
        parse_mock.return_value = self.request_mock
        self.mongo_mock.get.return_value = self.request_mock

        instance_mock = Mock(status="RUNNING")
        type(instance_mock).name = PropertyMock(return_value="default")
        system_mock.get.return_value = Mock(instances=[instance_mock])

        response = self.fetch(
            "/api/v1/requests",
            method="POST",
            body="",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(201, response.code)
        self.assertEqual("RUNNING", response.headers["Instance-Status"])
        self.assertTrue(self.request_mock.save.called)
        self.client_mock.processRequest.assert_called_once_with(self.request_mock.id)

    @patch("brew_view.controllers.request_list_api.MongoParser.parse_request")
    @patch("brew_view.controllers.request_list_api.thrift_context")
    def test_post_invalid(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.processRequest.return_value = self.future_mock
        self.future_mock.set_exception(bg_utils.bg_thrift.InvalidRequest())
        parse_mock.return_value = self.request_mock

        response = self.fetch(
            "/api/v1/requests",
            method="POST",
            body="",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.code, 400)
        self.assertTrue(self.request_mock.delete.called)
        self.assertTrue(self.client_mock.processRequest.called)

    @patch("brew_view.controllers.request_list_api.MongoParser.parse_request")
    @patch("brew_view.controllers.request_list_api.thrift_context")
    def test_post_publishing_exception(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.processRequest.return_value = self.future_mock
        self.future_mock.set_exception(bg_utils.bg_thrift.PublishException())
        parse_mock.return_value = self.request_mock

        response = self.fetch(
            "/api/v1/requests",
            method="POST",
            body="",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.code, 502)
        self.assertTrue(self.request_mock.delete.called)

    @patch("brew_view.controllers.request_list_api.MongoParser.parse_request")
    @patch("brew_view.controllers.request_list_api.thrift_context")
    def test_post_exception(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.future_mock.set_exception(Exception())
        parse_mock.return_value = self.request_mock

        response = self.fetch(
            "/api/v1/requests",
            method="POST",
            body="",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.code, 500)
        self.assertTrue(self.request_mock.delete.called)

    def test_post_no_content_type(self):
        response = self.fetch(
            "/api/v1/requests",
            method="POST",
            body="",
            headers={"content-type": "text/plain"},
        )
        self.assertEqual(response.code, 400)

    @patch("brew_view.controllers.request_list_api.MongoParser.parse_request")
    @patch("brew_view.controllers.request_list_api.thrift_context")
    def test_post_instance_status_exception(self, context_mock, parse_mock):
        context_mock.return_value = self.fake_context
        self.client_mock.processRequest.return_value = self.future_mock
        self.future_mock.set_result(None)
        parse_mock.return_value = self.request_mock
        self.mongo_mock.get.return_value = self.request_mock

        response = self.fetch(
            "/api/v1/requests",
            method="POST",
            body="",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(201, response.code)
        self.assertIn("Instance-Status", response.headers)
        self.assertEqual("UNKNOWN", response.headers["Instance-Status"])


@pytest.mark.usefixtures("mongo")
class TestRequestListAPI(object):
    @pytest.fixture
    def columns(self):
        def _factory(filter_value=None):
            filter_value = filter_value or {}

            columns = [
                {
                    "data": "command",
                    "name": "",
                    "searchable": True,
                    "orderable": True,
                    "search": {
                        "value": filter_value.get("command", ""),
                        "regex": False,
                    },
                },
                {
                    "data": "system",
                    "name": "",
                    "searchable": True,
                    "orderable": True,
                    "search": {"value": filter_value.get("system", ""), "regex": False},
                },
                {
                    "data": "instance_name",
                    "name": "",
                    "searchable": True,
                    "orderable": True,
                    "search": {
                        "value": filter_value.get("instance_name", ""),
                        "regex": False,
                    },
                },
                {
                    "data": "status",
                    "name": "",
                    "searchable": True,
                    "orderable": True,
                    "search": {"value": filter_value.get("status", ""), "regex": False},
                },
                {
                    "data": "created_at",
                    "name": "",
                    "searchable": True,
                    "orderable": True,
                    "search": {
                        "value": filter_value.get("created_at", ""),
                        "regex": False,
                    },
                },
                {
                    "data": "comment",
                    "name": "",
                    "searchable": True,
                    "orderable": True,
                    "search": {
                        "value": filter_value.get("comment", ""),
                        "regex": False,
                    },
                },
                {
                    "data": "metadata",
                    "name": "",
                    "searchable": True,
                    "orderable": True,
                    "search": {
                        "value": filter_value.get("metadata", ""),
                        "regex": False,
                    },
                },
                {"data": "id"},
            ]

            return [json.dumps(column) for column in columns]

        return _factory

    @pytest.fixture
    def order(self):
        def _factory(order_column):
            if order_column is not None:
                return [json.dumps({"column": order_column, "dir": "desc"})]
            return None

        return _factory

    @pytest.fixture
    def search(self):
        def _factory(search_value=None):
            if search_value is not None:
                return [json.dumps({"value": search_value, "regex": False})]
            return None

        return _factory

    @pytest.fixture
    def handler(self, monkeypatch):
        monkeypatch.setattr(brew_view, "config", Mock())
        return RequestListAPI(MagicMock(), MagicMock())

    @pytest.mark.parametrize(
        "include_children, order_column,filter_value,index",
        [
            # # Parent requests only
            # Nothing
            (False, None, None, "parent_index"),
            # Only sorting
            (False, 0, None, "parent_command_index"),
            (False, 1, None, "parent_system_index"),
            (False, 2, None, "parent_instance_name_index"),
            (False, 3, None, "parent_status_index"),
            (False, 4, None, "parent_created_at_index"),
            # Only filtering
            (False, None, {"command": "say"}, "parent_command_index"),
            (False, None, {"system": "test"}, "parent_system_index"),
            (False, None, {"instance_name": "say"}, "parent_instance_name_index"),
            (False, None, {"status": "SUCCESS"}, "parent_status_index"),
            (False, None, {"created_at": "start~stop"}, "parent_created_at_index"),
            # Both, but only applicable for created_at sorting
            (False, 4, {"command": "say"}, "parent_created_at_command_index"),
            (False, 4, {"system": "test"}, "parent_created_at_system_index"),
            (False, 4, {"instance_name": "s"}, "parent_created_at_instance_name_index"),
            (False, 4, {"status": "SUCCESS"}, "parent_created_at_status_index"),
            (False, 4, {"created_at": "start~stop"}, "parent_created_at_index"),
            # # All requests
            # Nothing
            (True, None, None, -1),  # Let mongo deal with this one
            # Only sorting
            (True, 0, None, "command_index"),
            (True, 1, None, "system_index"),
            (True, 2, None, "instance_name_index"),
            (True, 3, None, "status_index"),
            (True, 4, None, "created_at_index"),
            # Only filtering
            (True, None, {"command": "say"}, "command_index"),
            (True, None, {"system": "test"}, "system_index"),
            (True, None, {"instance_name": "say"}, "instance_name_index"),
            (True, None, {"status": "SUCCESS"}, "status_index"),
            (True, None, {"created_at": "start~stop"}, "created_at_index"),
            # Both, but only applicable for created_at sorting
            (True, 4, {"command": "say"}, "created_at_command_index"),
            (True, 4, {"system": "test"}, "created_at_system_index"),
            (True, 4, {"instance_name": "s"}, "created_at_instance_name_index"),
            (True, 4, {"status": "SUCCESS"}, "created_at_status_index"),
            (True, 4, {"created_at": "start~stop"}, "created_at_index"),
        ],
    )
    def test_order_index_hints(
        self,
        monkeypatch,
        handler,
        columns,
        order,
        include_children,
        order_column,
        filter_value,
        index,
    ):

        args = {
            "columns": columns(filter_value),
            "order": order(order_column),
            "include_children": [str(include_children)],
        }

        if order_column is None:
            del args["order"]

        monkeypatch.setattr(handler.request, "query_arguments", args)

        query_set, _ = handler._get_query_set()
        assert query_set._hint == index

    @pytest.mark.parametrize(
        "order_column,filter_value",
        [
            (None, None),  # Neither
            (0, None),  # Only sorting
            (None, {"command": "say"}),  # Only filtering
            (4, {"command": "say"}),  # Both
        ],
    )
    def test_overall_search_no_hint(
        self, monkeypatch, handler, columns, order, order_column, filter_value, search
    ):

        args = {
            "columns": columns(filter_value),
            "order": order(order_column),
            "search": search("Search Text"),
        }

        if order_column is None:
            del args["order"]

        monkeypatch.setattr(handler.request, "query_arguments", args)

        query_set, _ = handler._get_query_set()
        assert query_set._hint == -1
