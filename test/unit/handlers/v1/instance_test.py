# -*- coding: utf-8 -*-
from mock import MagicMock, Mock, patch

from .. import TestHandlerBase


class InstanceAPITest(TestHandlerBase):
    def setUp(self):
        self.instance_mock = Mock()

        mongo_patcher = patch("mongoengine.queryset.manager.QuerySetManager.__get__")
        self.addCleanup(mongo_patcher.stop)
        get_mock = mongo_patcher.start()
        get_mock.return_value.get.return_value = self.instance_mock

        serialize_patcher = patch(
            "brew_view.handlers.v1.instance.MongoParser.serialize_instance"
        )
        self.addCleanup(serialize_patcher.stop)
        self.serialize_mock = serialize_patcher.start()
        self.serialize_mock.return_value = "serialized_instance"

        self.client_mock = Mock(name="client_mock")
        self.fake_context = MagicMock(
            __enter__=Mock(return_value=self.client_mock),
            __exit__=Mock(return_value=False),
        )

        super(InstanceAPITest, self).setUp()

    def test_get(self):
        response = self.fetch("/api/v1/instances/id")
        output = response.body.decode("utf-8")
        self.assertEqual("serialized_instance", output)
        self.assertIn(self.instance_mock, self.serialize_mock.call_args[0])

    @patch("brew_view.handlers.v1.instance.thrift_context")
    def test_patch_initialize(self, context_mock):
        context_mock.return_value = self.fake_context

        self.fetch(
            "/api/v1/instances/id",
            method="PATCH",
            body='{"operations": [{"operation": "initialize"}]}',
            headers={"content-type": "application/json"},
        )
        self.client_mock.initializeInstance.assert_called_once_with("id")

    @patch("brew_view.handlers.v1.instance.thrift_context")
    def test_patch_start(self, context_mock):
        context_mock.return_value = self.fake_context

        self.fetch(
            "/api/v1/instances/id",
            method="PATCH",
            body='{"operations": [{"operation": "start"}]}',
            headers={"content-type": "application/json"},
        )
        self.client_mock.startInstance.assert_called_once_with("id")

    @patch("brew_view.handlers.v1.instance.thrift_context")
    def test_patch_stop(self, context_mock):
        context_mock.return_value = self.fake_context

        self.fetch(
            "/api/v1/instances/id",
            method="PATCH",
            body='{"operations": [{"operation": "stop"}]}',
            headers={"content-type": "application/json"},
        )
        self.client_mock.stopInstance.assert_called_once_with("id")

    @patch(
        "brew_view.handlers.v1.instance.datetime",
        Mock(utcnow=Mock(return_value="now")),
    )
    @patch("brew_view.handlers.v1.instance.thrift_context")
    def test_patch_heartbeat(self, context_mock):
        context_mock.return_value = self.fake_context

        self.fetch(
            "/api/v1/instances/id",
            method="PATCH",
            body='{"operations": [{"operation": "heartbeat"}]}',
            headers={"content-type": "application/json"},
        )
        self.assertEqual("now", self.instance_mock.status_info.heartbeat)

    @patch("brew_view.handlers.v1.instance.thrift_context")
    def test_patch_bad_operation(self, context_mock):
        context_mock.return_value = self.fake_context

        response = self.fetch(
            "/api/v1/instances/id",
            method="PATCH",
            body='{"operations": [{"operation": "fake"}]}',
            headers={"content-type": "application/json"},
        )
        self.assertGreaterEqual(response.code, 400)
