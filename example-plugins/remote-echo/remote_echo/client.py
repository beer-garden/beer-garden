from brewtils.decorators import register, command_registrar, plugin_param
from config import DEFAULT_MESSAGE


@command_registrar
class EchoClient(object):
    """A Client that simply echo's thing to STDOUT"""

    @plugin_param(key="message", description="The Message to be Echoed", optional=True, type="String", default=DEFAULT_MESSAGE)
    @plugin_param(key="loud", description="Determines if Exclamation marks are added", optional=True, type="Boolean", default=False)
    def say(self, message=DEFAULT_MESSAGE, loud=False):
        if loud:
            message += "!!!!!!!!!"

        return message

    @register(output_type='JSON')
    @plugin_param(key="message", description="The Message to be Echoed", optional=True, type="String",
                  default='{"str": "value", "nums": [1, 2, 17], "obj": {"nested": "awesome"}}')
    def say_json(self, message=DEFAULT_MESSAGE):
        """Echos with JSON output_type"""

        return message
