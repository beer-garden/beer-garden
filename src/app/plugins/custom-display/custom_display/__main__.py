import sys

from brewtils import command, get_connection_info, parameter, system, Plugin

__version__ = "1.0.0.dev0"


@system
class CustomDisplayClient(object):
    @command(form=[{"key": "parameters.message", "readonly": True}])
    @parameter(key="message", type="String", optional=False, nullable=False)
    def echo_message_custom_form_as_list(self, message="Can't change me! Hahaha!"):
        """form=[{"key": "parameters.message", "readonly": True}]"""
        return message

    @command(
        form={
            "type": "fieldset",
            "items": [{"key": "parameters.message", "readonly": True}],
        }
    )
    @parameter(key="message", type="String", optional=False, nullable=False)
    def echo_message_custom_form_as_dict(self, message="Can't change me! Hahaha!"):
        """form={"type": "fieldset", "items": [{"key": "parameters.message", "readonly": True}]}"""
        return message

    @command(form="./resources/say_form.json")
    @parameter(key="message", type="String", optional=False, nullable=False)
    @parameter(key="loud", type="Boolean")
    def echo_message_custom_form_from_file(self, message="Hello world!", loud=False):
        """form='./resources/say_form.json'"""
        return message + "!!!!!!!!!" if loud else message

    @command(
        schema={
            "message": {
                "type": "string",
                "readonly": True,
                "default": "Default in schema!",
            }
        }
    )
    @parameter(key="message", type="String", optional=False, nullable=False)
    def echo_message_custom_schema(self, message="Can't change me! Hahaha!"):
        """schema={"message":{'type': 'string','readonly': True,'default':'Default in schema!'}}"""
        return message

    @command(template="./resources/minimalist.html")
    def echo_minimalist(self, message):
        return message

    @parameter(
        key="message",
        type="String",
        optional=False,
        nullable=False,
        form_input_type="textarea",
    )
    def echo_message_textarea(self, message):
        return message

    @parameter(
        key="messages",
        type="String",
        multi=True,
        optional=False,
        nullable=False,
        form_input_type="textarea",
    )
    def echo_message_list_textarea(self, messages):
        return messages

    @parameter(
        key="message",
        type="Dictionary",
        optional=False,
        nullable=False,
        form_input_type="textarea",
    )
    def echo_message_dictionary(self, message):
        return message


def main():
    Plugin(
        CustomDisplayClient(),
        name="custom-display",
        version=__version__,
        **get_connection_info(sys.argv[1:])
    ).run()


if __name__ == "__main__":
    main()
