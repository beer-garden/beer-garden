from brewtils.decorators import command, system, parameter
from echo.config import DEFAULT_MESSAGE


@system
class EchoClient:
    """A Client that simply echo's thing to STDOUT"""

    @parameter(key="message", description="The Message to be Echoed", optional=True, type="String",
               default=DEFAULT_MESSAGE)
    @parameter(key="loud", description="Determines if Exclamation marks are added", optional=True, type="Boolean",
               default=False)
    def say(self, message=DEFAULT_MESSAGE, loud=False):
        if loud:
            message += "!!!!!!!!!"

        return message

    @command(output_type='JSON')
    @parameter(key="message", description="The Message to be Echoed", optional=True, type="String",
               default='{"str": "value", "nums": [1, 2, 17], "obj": {"nested": "awesome"}}')
    def say_json(self, message=DEFAULT_MESSAGE):
        """Echos with JSON output_type"""

        return message
