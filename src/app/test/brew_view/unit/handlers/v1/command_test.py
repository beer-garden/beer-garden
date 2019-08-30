# -*- coding: utf-8 -*-
import mongoengine.errors
from mock import Mock, patch

from .. import TestHandlerBase


@patch(
    "brew_view.handlers.v1.command.Command.objects",
    Mock(get=Mock(return_value="command")),
)
class CommandAPITest(TestHandlerBase):
    @patch(
        "brew_view.handlers.v1.command.CommandAPI.parser",
        Mock(serialize_command=Mock(return_value="serialized_command")),
    )
    def test_get(self):
        response = self.fetch("/api/v1/commands/id")
        self.assertEqual("serialized_command", response.body.decode("utf-8"))


@patch(
    "brew_view.handlers.v1.command.Command.objects",
    Mock(all=Mock(return_value=["cmd1", "cmd2"])),
)
class CommandListAPITest(TestHandlerBase):
    @patch("brew_view.handlers.v1.command.CommandListAPI.parser")
    def test_get(self, parser_mock):
        parser_mock.serialize_command = Mock(return_value="serialized_commands")
        response = self.fetch("/api/v1/commands")
        self.assertEqual("serialized_commands", response.body.decode("utf-8"))
        parser_mock.serialize_command.assert_called_once_with(
            ["cmd1", "cmd2"], many=True, to_string=True
        )

    @patch("brew_view.handlers.v1.command.CommandListAPI.parser")
    def test_get_throw_does_not_exist_return_500(self, parser_mock):
        parser_mock.serialize_command = Mock(
            side_effect=mongoengine.errors.DoesNotExist
        )
        response = self.fetch("/api/v1/commands")
        self.assertEqual(response.code, 500)
