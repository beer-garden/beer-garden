import json
import unittest

from brewtils.errors import ModelValidationError
from mock import patch
from mongoengine.errors import DoesNotExist

from .handlers import TestHandlerBase


@unittest.skip("TODO")
class ErrorHandlerTest(TestHandlerBase):
    def setUp(self):
        objects_patcher = patch("brew_view.handlers.v1.command.Command.objects")
        self.addCleanup(objects_patcher.stop)
        self.objects_mock = objects_patcher.start()

        super(ErrorHandlerTest, self).setUp()

    def test_type_match(self):
        e = ModelValidationError("error message")
        self.objects_mock.get.side_effect = e

        response = self.fetch("/api/v1/commands/id")
        self.assertEqual(400, response.code)
        self.assertEqual(json.dumps({"message": str(e)}), response.body.decode("utf-8"))

    def test_subtype_match(self):
        class TestValidationError(ModelValidationError):
            pass

        e = TestValidationError("key", "error message")
        self.objects_mock.get.side_effect = e

        response = self.fetch("/api/v1/commands/id")
        self.assertEqual(400, response.code)
        self.assertEqual(json.dumps({"message": str(e)}), response.body.decode("utf-8"))

    def test_no_type_match(self):
        class UnknownError(Exception):
            pass

        e = UnknownError()
        self.objects_mock.get.side_effect = e

        response = self.fetch("/api/v1/commands/id")
        self.assertEqual(500, response.code)
        self.assertIsNotNone(json.loads(response.body.decode("utf-8")).get("message"))

    def test_message_override(self):
        e = DoesNotExist()
        e.message = "The limit does not exist"
        self.objects_mock.get.side_effect = e

        response = self.fetch("/api/v1/commands/id")
        output = json.loads(response.body.decode("utf-8"))
        self.assertEqual(404, response.code)
        self.assertIsNotNone(output.get("message"))
        self.assertNotEqual(e.message, output.get("message"))
