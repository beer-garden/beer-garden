import sys

from brewtils import command, get_connection_info, parameter, system, Plugin

__version__ = "1.0.0.dev0"


@system
class EchoClient(object):
    """Client that echos things"""

    @parameter(
        key="message",
        type="String",
        description="The Message to be Echoed",
        optional=True,
        default="Hello, World!",
    )
    @parameter(
        key="loud",
        type="Boolean",
        description="Determines if Exclamation marks are added",
        optional=True,
        default=False,
    )
    def say(self, message, loud):
        """Echos!"""
        return message + "!!!!!!!!!" if loud else message

    @command(output_type="JSON")
    @parameter(
        key="message",
        type="String",
        description="The Message to be Echoed",
        optional=True,
        default='{"str": "value", "nums": [1, 17], "obj": {"nested": "sweet"}}',
    )
    def say_json(self, message):
        """Echos with JSON output_type"""
        return message

    @command(output_type="HTML")
    @parameter(
        key="message",
        type="String",
        description="The Message to be Echoed",
        optional=True,
        default='<h1>Hello, World</h1>',
    )
    def say_html(self, message):
        """Echos with HTML output_type"""
        return message


def main():
    Plugin(
        EchoClient(),
        name="echo",
        version=__version__,
        **get_connection_info(sys.argv[1:])
    ).run()


if __name__ == "__main__":
    main()
