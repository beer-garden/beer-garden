# -*- coding: utf-8 -*-
import json

from mock import MagicMock, Mock, PropertyMock, patch
from tornado.gen import Future

from .. import TestHandlerBase


class QueueAPITest(TestHandlerBase):
    def setUp(self):
        self.client_mock = Mock(name="client_mock")
        self.fake_context = MagicMock(
            __enter__=Mock(return_value=self.client_mock),
            __exit__=Mock(return_value=False),
        )

        super(QueueAPITest, self).setUp()

    @patch("brew_view.handlers.v1.queue.thrift_context")
    def test_delete_calls(self, context_mock):
        context_mock.return_value = self.fake_context

        self.fetch("/api/v1/queues/name", method="DELETE")
        self.client_mock.clearQueue.assert_called_once_with("name")


class QueueListAPITest(TestHandlerBase):
    def setUp(self):
        self.instance_mock = Mock(status="RUNNING")
        type(self.instance_mock).name = PropertyMock(return_value="default")
        self.system_mock = Mock(
            id="1234",
            display_name="display",
            version="1.0.0",
            instances=[self.instance_mock],
        )
        type(self.system_mock).name = PropertyMock(return_value="system_name")
        self.queue_name = "%s[%s]-%s" % (
            self.system_mock.name,
            self.instance_mock.name,
            self.system_mock.version,
        )

        self.client_mock = Mock(name="client_mock")
        self.fake_context = MagicMock(
            __enter__=Mock(return_value=self.client_mock),
            __exit__=Mock(return_value=False),
        )
        self.future_mock = Future()

        super(QueueListAPITest, self).setUp()

    @patch("brew_view.handlers.v1.queue.System.objects")
    def test_get_empty(self, objects_mock):
        objects_mock.all.return_value.select_related = Mock(return_value=[])

        response = self.fetch("/api/v1/queues")
        self.assertEqual("[]", response.body.decode("utf-8"))

    @patch("brew_view.handlers.v1.queue.thrift_context")
    @patch("brew_view.handlers.v1.queue.System.objects")
    def test_get(self, objects_mock, context_mock):
        objects_mock.all.return_value.select_related = Mock(
            return_value=[self.system_mock]
        )
        context_mock.return_value = self.fake_context

        queue_return_mock = Mock(size=1)
        type(queue_return_mock).name = PropertyMock(return_value=self.queue_name)
        self.client_mock.getQueueInfo.return_value = self.future_mock
        self.future_mock.set_result(queue_return_mock)

        response = self.fetch("/api/v1/queues")
        output = json.loads(response.body.decode("utf-8"))
        self.client_mock.getQueueInfo.assert_called_once_with(
            self.system_mock.name, self.system_mock.version, self.instance_mock.name
        )
        self.assertEqual(1, len(output))
        self.assertDictEqual(
            {
                "system": self.system_mock.name,
                "display": self.system_mock.display_name,
                "version": self.system_mock.version,
                "system_id": self.system_mock.id,
                "instance": self.instance_mock.name,
                "name": self.queue_name,
                "size": 1,
            },
            output[0],
        )

    @patch("brew_view.handlers.v1.queue.thrift_context")
    @patch("brew_view.handlers.v1.queue.System.objects")
    def test_get_with_exception(self, objects_mock, context_mock):
        objects_mock.all.return_value.select_related = Mock(
            return_value=[self.system_mock]
        )
        context_mock.return_value = self.fake_context
        self.client_mock.getVersion.return_value = self.future_mock
        self.future_mock.set_exception(ValueError("ERROR"))

        response = self.fetch("/api/v1/queues")
        output = json.loads(response.body.decode("utf-8"))
        self.assertEqual(1, len(output))
        self.assertEqual(
            {
                "system": self.system_mock.name,
                "display": self.system_mock.display_name,
                "version": self.system_mock.version,
                "system_id": self.system_mock.id,
                "instance": self.instance_mock.name,
                "name": "UNKNOWN",
                "size": -1,
            },
            output[0],
        )

    @patch("brew_view.handlers.v1.queue.thrift_context")
    @patch("brew_view.handlers.v1.queue.System.objects")
    def test_delete(self, objects_mock, context_mock):
        objects_mock.all = Mock(return_value=[self.system_mock])
        context_mock.return_value = self.fake_context
        self.client_mock.clearAllQueues.return_value = self.future_mock
        self.future_mock.set_result(None)

        response = self.fetch("/api/v1/queues", method="DELETE")
        self.assertEqual(204, response.code)
        self.client_mock.clearAllQueues.assert_called_once_with()
