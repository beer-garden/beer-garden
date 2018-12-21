from mock import Mock, patch

from . import TestHandlerBase


@patch(
    "brew_view.controllers.command_api.Command.objects",
    Mock(get=Mock(return_value="command")),
)
class CommandAPITest(TestHandlerBase):
    @patch(
        "brew_view.controllers.command_api.CommandAPI.parser",
        Mock(serialize_command=Mock(return_value="serialized_command")),
    )
    def test_get(self):
        response = self.fetch("/api/v1/commands/id")
        self.assertEqual("serialized_command", response.body.decode("utf-8"))
