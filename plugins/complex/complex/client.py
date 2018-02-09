import json
import logging
import os

from complex.model import MyModel, MyNestedModel, MyListModel, MyModelWithDefaults

from brewtils.decorators import command, system, parameter


@system
class ComplexClient:
    """A Client that simply echo's thing to STDOUT"""

    def __init__(self, host, port):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port

    @parameter(key="b", type="Boolean", description="Just want to test Booleans", multi=False,
               display_name="A Boolean", optional=False, default=None, choices=None, model=None,
               nullable=False)
    def echo_bool(self, b):
        self.logger.info("Is Bool? : %s" % isinstance(b, bool))
        return b

    @parameter(key="b", type="Boolean", description="Testing a nullable boolean", multi=False,
               display_name="A boolean",
               optional=False, default=None, nullable=True)
    def echo_boolean_nullable(self, b):
        self.logger.info(b)
        return b

    @parameter(key="b", type="Boolean", description="Testing a nullable boolean", multi=False,
               display_name="A boolean",
               optional=False, default=True, nullable=True)
    def echo_boolean_nullable_with_true_default(self, b=True):
        self.logger.info(b)
        return b

    @parameter(key="b", type="Boolean", description="Testing a Boolean with a false default",
               multi=False,
               display_name="A Boolean", optional=True, default=False, nullable=False)
    def echo_boolean_optional_with_false_default(self, b=False):
        self.logger.info(b)
        return b

    @parameter(key="f", type="Float", description="Just want to test Floats", multi=False,
               display_name="A Float",
               optional=False, default=None, choices=None, model=None, nullable=False)
    def echo_float(self, f):
        self.logger.info("%.2f" % f)
        return f

    @parameter(key="i", type="Integer", description="Just want to test Integers", multi=False,
               display_name="An Integer", optional=False, default=None, choices=None, model=None,
               nullable=False)
    def echo_integer(self, i):
        self.logger.info("%d" % i)
        return i

    @parameter(key="date", type="Date", nullable=True, display_name="Date",
               description="No time component, nullable")
    @parameter(key="datetime", type="DateTime", display_name="DateTime",
               description="Time component, not nullable")
    def echo_dates(self, date, datetime):
        return date, datetime

    @parameter(key="i", type="Integer", description="Just want to test Integers", multi=False,
               display_name="An Integer", optional=False, default=None,
               choices=list(range(1, 101)),
               model=None,
               nullable=False)
    def echo_integer_with_lots_of_choices(self, i):
        self.logger.info("%d" % i)
        return i

    @parameter(key="model", optional=False, description="A Model with a cool definition.",
               model=MyListModel)
    def echo_list_model(self, model):
        for k, v in model.items():
            self.logger.info('{"%s" : %s}' % (k, v))
        return model

    @parameter(key="list_of_b", type="Boolean", description="Testing List of Booleans", multi=True,
               display_name="A List of Booleans", optional=False, default=None, choices=None,
               model=None,
               nullable=False)
    def echo_list_of_booleans(self, list_of_b):
        for b in list_of_b:
            self.logger.info("%s" % b)
        return list_of_b

    @parameter(key="list_of_b", type="Boolean", description="Testing List of Booleans", multi=True,
               display_name="A List of Booleans", optional=False, default=None, choices=None,
               model=None,
               nullable=False, maximum=2)
    def echo_list_of_booleans_with_maximum(self, list_of_b):
        for b in list_of_b:
            self.logger.info("%s" % b)
        return list_of_b

    @parameter(key="list_of_b", type="Boolean", description="Testing List of Booleans", multi=True,
               display_name="A List of Booleans", optional=False, default=None, choices=None,
               model=None,
               nullable=False, minimum=2)
    def echo_list_of_booleans_with_minimum(self, list_of_b):
        for b in list_of_b:
            self.logger.info("%s" % b)
        return list_of_b

    @parameter(key="list_of_i", type="Integer", description="Testing List of Integers", multi=True,
               display_name="A List of Integers", optional=False, default=None, choices=None,
               model=None,
               nullable=False)
    def echo_list_of_integers(self, list_of_i):
        for i in list_of_i:
            self.logger.info("%d" % i)
        return list_of_i

    @parameter(key="list_of_s", type="String", description="Testing List of Strings", multi=True,
               display_name="A List of Strings", optional=False, default=None, choices=None,
               model=None,
               nullable=False)
    def echo_list_of_strings(self, list_of_s):
        for s in list_of_s:
            self.logger.info("%s" % s)
        return list_of_s

    @parameter(key="list_of_s", type="String", description="Testing List of Strings", multi=True,
               display_name="A List of Strings", optional=False, default=None,
               choices=['a', 'b', 'c'], model=None,
               nullable=False)
    def echo_list_of_strings_with_choices(self, list_of_s):
        for s in list_of_s:
            self.logger.info("%s" % s)
        return list_of_s

    @parameter(key="list_of_s", type="String", description="Testing List of Strings", multi=True,
               display_name="A List of Strings", optional=True, default=['a', 'b', 'c'],
               choices=None, model=None,
               nullable=False)
    def echo_list_of_strings_with_default(self, list_of_s=None):
        list_of_s = list_of_s or ['a', 'b', 'c']
        for s in list_of_s:
            self.logger.info("%s" % s)
        return list_of_s

    @parameter(key="list_of_s", type="String", description="Testing List of Strings", multi=True,
               display_name="A List of Strings", optional=False, default=['a', 'b', 'c'],
               choices=None, model=None,
               nullable=False)
    def echo_list_of_strings_with_default_required(self, list_of_s=None):
        list_of_s = list_of_s or ['a', 'b', 'c']
        for s in list_of_s:
            self.logger.info("%s" % s)
        return list_of_s

    @command(output_type="JSON")
    def echo_message_huge_json(self):
        d = {n: True for n in range(2000)}
        return json.dumps(d)

    @command(command_type="INFO")
    @parameter(key="message", type="String", optional=False, nullable=False)
    def echo_message_info(self, message):
        if message is None:
            raise ValueError("Message cannot be None.")

        self.logger.info(message)
        return message

    @parameter(key="model", optional=False, description="A Model with a cool definition.",
               model=MyModel)
    def echo_model(self, model):
        for k, v in model.items():
            self.logger.info('{"%s" : %s}' % (k, v))
        return model

    @parameter(key="model", optional=True, nullable=True, description="A optional model.",
               model=MyModel)
    def echo_model_optional(self, model):
        if model:
            for k, v in model.items():
                self.logger.info('{"%s" : %s}' % (k, v))
        return model

    @parameter(key="models", optional=False, description="A List of Models",
               model=MyNestedModel, multi=True)
    def echo_model_simple_list(self, models):
        for model in models:
            for k, v in model.items():
                self.logger.info('{"%s" : %s}' % (k, v))
        return models

    @parameter(key="models", optional=False, description="A List of Models",
               model=MyNestedModel, multi=True,
               default=[{"my_nested_string": "str1", "my_nested_int": 1},
                        {"my_nested_string": "str2", "my_nested_int": 2}])
    def echo_model_simple_list_with_default(self, models):
        for model in models:
            for k, v in model.items():
                self.logger.info('{"%s" : %s}' % (k, v))
        return models

    @parameter(key="model", optional=False, description="A Model with a cool definition.",
               model=MyModelWithDefaults,
               default={"my_foo": "clientFooValue", "my_bar": "clientBarValue"})
    def echo_model_with_nested_defaults(self, model):
        for k, v in model.items():
            self.logger.info('{"%s" : %s}' % (k, v))
        return model

    @parameter(key="model", optional=False, description="A Model with a cool definition.",
               model=MyModelWithDefaults)
    def echo_model_with_nested_defaults_no_main(self, model):
        for k, v in model.items():
            self.logger.info('{"%s" : %s}' % (k, v))
        return model

    @parameter(key="messages", optional=True, nullable=True, multi=True,
               description="This message could be any valid JSON value.",
               default=["a", 1, True, None])
    def echo_optional_any_multi_message_with_default(self, messages):
        for message in messages:
            self.logger.info(message.__class__)
            self.logger.info(message)
        return messages

    # PAY ATTENTION TO THIS ONE
    @parameter(key="message", optional=True, nullable=False, default="default required",
               type="String")
    def echo_optional_message_nullable_false(self, message="default required"):
        self.logger.info(message)
        return message

    @parameter(key="message", optional=True, nullable=True, type="String")
    def echo_optional_message_nullable_true_no_default(self, message):
        if not message:
            self.logger.info("No message provided, and that's okay.")
        else:
            self.logger.info(message)

        return message

    @parameter(key="message", optional=True, nullable=True, default="can be null", type="String")
    def echo_optional_message_nullable_true_non_default(self, message="can be null"):
        if not message:
            self.logger.info("No message provided, and that's okay.")
        else:
            self.logger.info(message)

        return message

    @parameter(key="message", optional=True, nullable=True, default=None, type="String")
    def echo_optional_message_nullable_true_null_default(self, message=None):
        if not message:
            self.logger.info("No message provided, and that's okay.")
        else:
            self.logger.info(message)

        return message

    @parameter(key="model", optional=True, nullable=True, model=MyModelWithDefaults,
               description="An optional model with defaults")
    def echo_optional_model_with_defaults(self, model):
        return model

    @parameter(key='param', optional=True, nullable=True, multi=True, model=MyNestedModel)
    def echo_optional_multi_nullable_model(self, param):
        return param

    @parameter(key='param', optional=True, nullable=True, multi=True, model=MyModelWithDefaults,
               default=[{'my_foo': 'foo', 'my_bar': 'bar'}])
    def echo_optional_multi_nullable_model_with_both_defaults(self, param):
        return param

    @parameter(key='param', optional=True, nullable=True, multi=True, model=MyModelWithDefaults)
    def echo_optional_multi_nullable_model_with_model_defaults(self, param):
        return param

    @parameter(key='param', optional=True, nullable=True, multi=True, model=MyNestedModel,
               default=[{'my_nested_string': 'hi', 'my_nested_int': 2}])
    def echo_optional_multi_nullable_model_with_multi_defaults(self, param):
        return param

    @parameter(key='param', optional=True, nullable=True, multi=True, type='String',
               default=['hello', 'there'])
    def echo_optional_multi_nullable_string(self, param):
        return param

    @parameter(key="d", type="Dictionary", description="Testing a Blank Dictionary", multi=False,
               display_name="A Dictionary", optional=False, default=None, choices=None,
               model=None, nullable=False)
    def echo_raw_dictionary(self, d):
        for k, v in d.items():
            self.logger.info("%s : %s" % (k, v))
        return d

    @parameter(key="d", type="Dictionary", description="Testing a Blank Dictionary", multi=False,
               display_name="A Dictionary", optional=False, default=None, choices=None,
               model=None, nullable=True)
    def echo_raw_dictionary_nullable(self, d=None):
        if d is not None:
            for k, v in d.items():
                self.logger.info("%s : %s" % (k, v))
        return d

    @parameter(key="d", type="Dictionary", description="Testing a Blank Dictionary", multi=False,
               display_name="A Dictionary", optional=True, default=None, choices=None,
               model=None, nullable=True)
    def echo_raw_dictionary_optional(self, d=None):
        if d is not None:
            for k, v in d.items():
                self.logger.info("%s : %s" % (k, v))
        return d

    @parameter(key="d", type="Dictionary", description="Testing a Blank Dictionary", multi=False,
               display_name="A Dictionary", optional=True, default={"foo": "bar"}, choices=None,
               model=None,
               nullable=False)
    def echo_raw_dictionary_optional_with_default(self, d=None):
        d = d or {"foo": "bar"}
        for k, v in d.items():
            self.logger.info("%s : %s" % (k, v))
        return d

    @parameter(key="d", type="Dictionary", description="Testing a Blank Dictionary", multi=False,
               display_name="A Dictionary", optional=True, default=None, choices=None,
               model=None, nullable=True,
               maximum=2)
    def echo_raw_dictionary_optional_with_maximum(self, d=None):
        if d is not None:
            for k, v in d.items():
                self.logger.info("%s : %s" % (k, v))
        return d

    @parameter(key="message", optional=False, nullable=False,
               description="This message could be any valid JSON value.")
    def echo_required_any_message(self, message):
        self.logger.info(message.__class__)
        self.logger.info(message)
        return message

    @parameter(key="messages", optional=False, nullable=False, multi=True,
               description="This message could be any valid JSON value.")
    def echo_required_any_multi_message(self, messages):
        for message in messages:
            self.logger.info(message.__class__)
            self.logger.info(message)
        return messages

    @parameter(key="messages", optional=False, nullable=True, multi=True,
               description="This message could be any valid JSON value.",
               default=["a", 1, True, None])
    def echo_required_any_multi_message_with_default(self, messages):
        for message in messages:
            self.logger.info(message.__class__)
            self.logger.info(message)
        return messages

    @parameter(key="message", optional=False, nullable=False, type="String")
    def echo_required_message(self, message):
        if message is None:
            raise ValueError("Message cannot be None.")

        self.logger.info(message)
        return message

    @parameter(key="message", optional=False, nullable=False, default=None, type="String")
    def echo_required_message_nullable_false_no_default(self, message=None):
        if message is None:
            raise ValueError("Message cannot be None even though the default is None.")

        self.logger.info(message)
        return message

    @parameter(key="message", optional=False, nullable=False, default="cannot be null",
               type="String")
    def echo_required_message_nullable_false_with_default(self, message="cannot be null"):
        if message is None:
            raise ValueError("Message cannot be None.")

        self.logger.info(message)
        return message

    @parameter(key="message", optional=False, nullable=True, type="String")
    def echo_required_message_nullable_true(self, message):
        if message:
            self.logger.info(message)

        return message

    @parameter(key="message", optional=False, nullable=True, default="can be null", type="String")
    def echo_required_message_nullable_true_with_non_null_default(self, message="can be null"):
        if message:
            self.logger.info(message)

        return message

    @parameter(key="message", optional=False, nullable=True, default=None, type="String")
    def echo_required_message_nullable_true_with_null_default(self, message=None):
        if message:
            self.logger.info(message)

        return message

    @parameter(key="message", type="String", optional=False, nullable=False, regex=r'^Hi.*')
    def echo_required_message_regex(self, message):
        if message is None:
            raise ValueError("Message cannot be None.")

        self.logger.info(message)
        return message

    @parameter(key="message", type="String", optional=False, nullable=True, regex=r'^Hi.*',
               default=None)
    def echo_required_nullable_message_regex(self, message=None):
        self.logger.info(message)
        return message

    @parameter(key="model", optional=False, description="A Model with a cool definition.",
               model=MyNestedModel)
    def echo_simple_model(self, model):
        for k, v in model.items():
            self.logger.info('{"%s" : %s}' % (k, v))
        return model

    @parameter(key="model", optional=False, description="A Model with a cool definition.",
               model=MyNestedModel,
               default={"my_nested_string": "foo", "my_nested_int": 1})
    def echo_simple_model_with_default(self, model):
        for k, v in model.items():
            self.logger.info('{"%s" : %s}' % (k, v))
        return model

    @parameter(key="s", type="String", description="Just want to test Small Choices", multi=False,
               display_name="A String", optional=False, default=None,
               choices=["a", "b", "c", "d", "e"], model=None,
               nullable=False)
    def echo_string_with_small_choices(self, s):
        self.logger.info("Is in choices?: %s" % (s in ['a', 'b', 'c', 'd', 'e']))
        return s

    @parameter(key="echo_max_value", type="Integer",
               description="Testing integer maximum constraint", multi=False,
               display_name="An Integer", optional=False, nullable=False, maximum=20)
    def echo_with_max_value(self, echo_max_value):
        self.logger.info(echo_max_value)
        return echo_max_value

    @parameter(key="echo_string", type="String",
               description="Testing string maximum constraint", multi=False,
               display_name="A String", optional=False, nullable=False, maximum=10)
    def echo_with_max_value_string(self, echo_string):
        self.logger.info(echo_string)
        return echo_string

    @parameter(key="echo_min_value", type="Integer",
               description="Testing integer minimum constraint", multi=False,
               display_name="An Integer", optional=False, nullable=False, minimum=10)
    def echo_with_min_value(self, echo_min_value):
        self.logger.info(echo_min_value)
        return echo_min_value

    @parameter(key="echo_string", type="String",
               description="Testing string minimum constraint", multi=False,
               display_name="A String", optional=False, nullable=False, minimum=3)
    def echo_with_min_value_string(self, echo_string):
        self.logger.info(echo_string)
        return echo_string

    @command
    def ping(self):
        self.logger.info("Ping")

    @command
    def prove_env(self):
        """Prints out the DB_NAME and DB_PASS from the environment, just to prove it works"""
        self.logger.info("Proving the Environment Variables are there.")
        self.logger.info("DB Name    : %s" % os.getenv('DB_NAME'))
        self.logger.info("DB Password: %s" % os.getenv('DB_PASS'))
        self.logger.info("Told you they were here!")
        return json.dumps({'DB_NAME': os.getenv('DB_NAME'), 'DB_PASS': os.getenv('DB_PASS')})

    @parameter(key="system", type="String", optional=False, nullable=False, is_kwarg=True)
    @parameter(key="command", type="String", optional=False, nullable=False, is_kwarg=True)
    @parameter(key="comment", type="String", optional=False, nullable=False, is_kwarg=True)
    @parameter(key="system_version", type="String", optional=False, nullable=False, is_kwarg=True)
    @parameter(key="instance_name", type="String", optional=False, nullable=False, is_kwarg=True)
    @parameter(key="parameters", type="String", optional=False, nullable=False, multi=True,
               is_kwarg=True)
    def weird_parameter_names(self, **kwargs):
        return json.dumps(kwargs)
