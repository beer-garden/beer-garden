import unittest
import json
from helper import RequestGenerator, setup_easy_client, wait_for_response
from helper.assertions import *


class ComplexText(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.easy_client = setup_easy_client()

    def setUp(self):
        self.system = "complex"
        self.system_version = "1.0.0.dev"
        self.instance_name = "c1"
        self.request_generator = RequestGenerator(system=self.system, system_version=self.system_version,
                                                  instance_name=self.instance_name)

    def test_invalid_instance_name(self):
        request = self.request_generator.generate_request(instance_name="INVALID_NAME", command="ping")
        assert_validation_error(self, self.easy_client, request)

    def test_invalid_system_name(self):
        request = self.request_generator.generate_request(system="BAD_SYSTEM_NAME", command="ping")
        assert_validation_error(self, self.easy_client, request)

    def test_invalid_system_version(self):
        request = self.request_generator.generate_request(system_version="INVALID_VERSION", command="ping")
        assert_validation_error(self, self.easy_client, request)

    def test_invalid_command(self):
        request = self.request_generator.generate_request(command="INVALID_COMMAND")
        assert_validation_error(self, self.easy_client, request)

    def test_good_ping(self):
        request = self.request_generator.generate_request(command="ping")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)

    def test_ping_with_invalid_parameters(self):
        request = self.request_generator.generate_request(command="ping", parameters={"foo": "bar"})
        assert_validation_error(self, self.easy_client, request)

    def test_ping_with_comment(self):
        request = self.request_generator.generate_request(command="ping", comment="comment_text")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, comment="comment_text")

    def test_boolean_good(self):
        request = self.request_generator.generate_request(command="echo_bool", parameters={"b": True})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="true")

    def test_boolean_bad_type(self):
        request = self.request_generator.generate_request(command="echo_bool", parameters={"b": "NOT_A_BOOL"})
        assert_validation_error(self, self.easy_client, request)

    def test_nullable_boolean_as_null(self):
        request = self.request_generator.generate_request(command="echo_boolean_nullable", parameters={"b": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_nullable_boolean_with_true_default_as_null(self):
        request = self.request_generator.generate_request(command="echo_boolean_nullable_with_true_default",
                                                          parameters={"b": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_nullable_boolean_with_true_not_in_param(self):
        request = self.request_generator.generate_request(command="echo_boolean_nullable_with_true_default",
                                                          parameters={})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="true")

    def test_optional_boolean_with_false_default(self):
        request = self.request_generator.generate_request(command="echo_boolean_optional_with_false_default")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="false")

    def test_echo_float_valid(self):
        request = self.request_generator.generate_request(command="echo_float",
                                                          parameters={"f": 1.2})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response,  output="1.2")

    def test_echo_float_invalid_type(self):
        request = self.request_generator.generate_request(command="echo_float",
                                                          parameters={"f": "INVALID_TYPE"})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_integer_valid(self):
        request = self.request_generator.generate_request(command="echo_integer",
                                                          parameters={"i": 1})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="1")

    def test_echo_integer_invalid_type(self):
        request = self.request_generator.generate_request(command="echo_integer",
                                                          parameters={"i": 1.2})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_integer_in_choice(self):
        request = self.request_generator.generate_request(command="echo_integer_with_lots_of_choices",
                                                          parameters={"i": 15})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="15")

    def test_echo_integer_invalid_choice(self):
        request = self.request_generator.generate_request(command="echo_integer_with_lots_of_choices",
                                                          parameters={"i": 1.5})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_integer_choice_out_of_range(self):
        request = self.request_generator.generate_request(command="echo_integer_with_lots_of_choices",
                                                          parameters={"i": -10})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_list_model(self):
        parameters = {"model": {"my_list_of_strings": ["a", "b", "c"], "my_choices_string": "a"}}
        request = self.request_generator.generate_request(command="echo_list_model",
                                                          parameters=parameters)
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertDictEqual(parameters['model'], json.loads(response.output))

    def test_echo_list_model_invalid_model_type(self):
        request = self.request_generator.generate_request(command="echo_list_model",
                                                          parameters={"model": ["SHOULD_BE_DICT"]})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_list_model_invalid_type_inside_list(self):
        request = self.request_generator.generate_request(command="echo_list_model",
                                                          parameters={"model": ["good", {"bad": "time"}]})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_list_model_null_inside_list_not_allowed(self):
        request = self.request_generator.generate_request(command="echo_list_model",
                                                          parameters={"model": ["good", None]})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_list_of_booleans(self):
        request = self.request_generator.generate_request(command="echo_list_of_booleans",
                                                          parameters={"list_of_b": [True, False]})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps([True, False]))

    def test_echo_list_of_booleans_with_maximum_good(self):
        request = self.request_generator.generate_request(command="echo_list_of_booleans_with_maximum",
                                                          parameters={"list_of_b": [True, False]})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps([True, False]))

    def test_echo_list_of_booleans_with_maximum_too_many(self):
        request = self.request_generator.generate_request(command="echo_list_of_booleans_with_maximum",
                                                          parameters={"list_of_b": [True, False, True]})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_list_of_booleans_with_minimum_good(self):
        request = self.request_generator.generate_request(command="echo_list_of_booleans_with_minimum",
                                                          parameters={"list_of_b": [True, False]})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps([True, False]))

    def test_echo_list_of_booleans_with_minimum_too_few(self):
        request = self.request_generator.generate_request(command="echo_list_of_booleans_with_minimum",
                                                          parameters={"list_of_b": [True]})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_list_of_integers(self):
        request = self.request_generator.generate_request(command="echo_list_of_integers",
                                                          parameters={"list_of_i": [1, 2]})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps([1, 2]))

    def test_echo_list_of_strings(self):
        request = self.request_generator.generate_request(command="echo_list_of_strings",
                                                          parameters={"list_of_s": ["1", "2"]})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps(["1", "2"]))

    def test_echo_list_of_strings_with_choices(self):
        request = self.request_generator.generate_request(command="echo_list_of_strings_with_choices",
                                                          parameters={"list_of_s": ["a", "b"]})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps(["a", "b"]))

    def test_echo_list_of_strings_with_choices_repeat_values(self):
        request = self.request_generator.generate_request(command="echo_list_of_strings_with_choices",
                                                          parameters={"list_of_s": ["a", "a"]})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps(["a", "a"]))

    def test_echo_list_of_strings_with_default(self):
        request = self.request_generator.generate_request(command="echo_list_of_strings_with_default",
                                                          parameters={})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps(["a", "b", "c"]))

    def test_echo_list_of_strings_with_default_required_no_list_provided(self):
        request = self.request_generator.generate_request(command="echo_list_of_strings_with_default_required",
                                                          parameters={})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps(['a', 'b', 'c']))

    def test_echo_list_of_strings_with_default_required_none_entry_provided(self):
        request = self.request_generator.generate_request(command="echo_list_of_strings_with_default_required",
                                                          parameters={"list_of_s": None})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_message_huge_json(self):
        request = self.request_generator.generate_request(command='echo_message_huge_json')
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)

    def test_echo_model(self):
        parameters = {
            'model': {
                'my_string': 'my_string',
                'my_string_with_choices': 'A',
                'my_int': 1,
                'my_float': 1.2,
                'my_bool': True,
                'my_any': ["this", "is", "an", "any"],
                'my_raw_dict': {"foo": "bar", "baz": [1, 2, 3], "null_thing": None, "dict": {"another": "dict"},
                                "ball": 1, "float": 1.2, "bool": False},
                'my_nested_model': {
                    'my_nested_string': "my_nested_string",
                    'my_nested_int': 2
                },
                'my_list_of_strings': ['a', 'b', 'c'],
                'my_optional_string': 'provided_anyway',
                'my_nullable_string': None,
                'my_list_of_models': [
                    {'my_list_of_strings': ['more', 'list', 'of', 'strings'], "my_choices_string": "a"},
                    {'my_list_of_strings': ['more', 'list', 'of', 'strings2'], "my_choices_string": "b"},
                ]
            }
        }
        request = self.request_generator.generate_request(command="echo_model",
                                                          parameters=parameters)
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertDictEqual(parameters['model'], json.loads(response.output))

    def test_echo_model_optional_not_provided(self):
        request = self.request_generator.generate_request(command="echo_model_optional")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_model_simple_list(self):
        parameters = {
            'models': [
                {'my_nested_string': "foo", "my_nested_int": 1},
                {'my_nested_string': "bar", "my_nested_int": 2},
                {'my_nested_string': "baz", "my_nested_int": 3}
            ]
        }
        request = self.request_generator.generate_request(command="echo_model_simple_list", parameters=parameters)
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertListEqual(parameters['models'], json.loads(response.output))

    def test_echo_model_simple_list_with_default(self):
        request = self.request_generator.generate_request(command="echo_model_simple_list_with_default")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertListEqual(json.loads(response.output), [
            {"my_nested_string": "str1", "my_nested_int": 1},
            {"my_nested_string": "str2", "my_nested_int": 2}
        ])

    def test_echo_model_with_nested_defaults_override(self):
        model = {"my_foo": "foo", "my_bar": "bar"}
        request = self.request_generator.generate_request(command="echo_model_with_nested_defaults",
                                                          parameters={"model": model})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps(model))

    def test_echo_model_with_nested_defaults_partial_fallback_to_model(self):
        model = {"my_foo": "foo"}
        request = self.request_generator.generate_request(command="echo_model_with_nested_defaults",
                                                          parameters={"model": model})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps({"my_foo": "foo", "my_bar": "defaultBarFromModel"}))

    def test_echo_model_with_nested_defaults_fallback_to_model_defaults(self):
        request = self.request_generator.generate_request(command="echo_model_with_nested_defaults",
                                                          parameters={"model": {}})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps({"my_foo": "defaultFooFromModel",
                                                               "my_bar": "defaultBarFromModel"}))

    def test_echo_model_with_nested_defaults_nothing_provided(self):
        request = self.request_generator.generate_request(command="echo_model_with_nested_defaults")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps({"my_foo": "clientFooValue", "my_bar": "clientBarValue"}))

    def test_echo_model_with_nested_defaults_invalid_key_provided(self):
        request = self.request_generator.generate_request(command="echo_model_with_nested_defaults",
                                                          parameters={"model": {"BAD_KEY": "abc"}})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_model_with_nested_defaults_no_main_nothing_provided(self):
        request = self.request_generator.generate_request(command="echo_model_with_nested_defaults_no_main")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps({"my_foo": "defaultFooFromModel",
                                                               "my_bar": "defaultBarFromModel"}))

    def test_echo_optional_any_multi_message_with_default(self):
        parameters = {"messages": [
            "foo",
            None,
            {"foo": "bar"},
            1,
            1.2,
            ["a", "b", "c"],
            True
        ]}
        request = self.request_generator.generate_request(command="echo_optional_any_multi_message_with_default",
                                                          parameters=parameters)
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertListEqual(json.loads(response.output), parameters['messages'])

    def test_echo_optional_message_nullable_false_null_provided(self):
        request = self.request_generator.generate_request(command="echo_optional_message_nullable_false",
                                                          parameters={"message": None})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_optional_message_nullable_false_no_key_provided(self):
        request = self.request_generator.generate_request(command="echo_optional_message_nullable_false",
                                                          parameters={})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)

    def test_echo_optional_message_nullable_true_no_default_no_key(self):
        request = self.request_generator.generate_request(command="echo_optional_message_nullable_true_no_default",
                                                          parameters={})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_optional_message_nullable_true_no_default_null(self):
        request = self.request_generator.generate_request(command="echo_optional_message_nullable_true_no_default",
                                                          parameters={"message": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_optional_message_nullable_true_non_null_default_no_key(self):
        request = self.request_generator.generate_request(command="echo_optional_message_nullable_true_non_default")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="can be null")

    def test_echo_optional_message_nullable_true_non_null_default_none(self):
        request = self.request_generator.generate_request(command="echo_optional_message_nullable_true_non_default",
                                                          parameters={"message": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_optional_model_with_defaults_no_key(self):
        request = self.request_generator.generate_request(command="echo_optional_model_with_defaults")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_optional_model_with_defaults_key_none(self):
        request = self.request_generator.generate_request(command="echo_optional_model_with_defaults",
                                                          parameters={"model": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_optional_model_with_defaults_empty_model(self):
        request = self.request_generator.generate_request(command="echo_optional_model_with_defaults",
                                                          parameters={"model": {}})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps({"my_foo": "defaultFooFromModel",
                                                               "my_bar": "defaultBarFromModel"}))

    def test_echo_optional_model_with_defaults_partial_model(self):
        request = self.request_generator.generate_request(command="echo_optional_model_with_defaults",
                                                          parameters={"model": {"my_foo": "provided"}})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps({"my_foo": "provided",
                                                               "my_bar": "defaultBarFromModel"}))

    def test_echo_optional_multi_nullable_model_empty_list_provided(self):
        request = self.request_generator.generate_request(command="echo_optional_multi_nullable_model",
                                                          parameters={"param": []})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="[]")

    def test_echo_optional_multi_nullable_model_none_provided(self):
        request = self.request_generator.generate_request(command="echo_optional_multi_nullable_model",
                                                          parameters={"param": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_optional_multi_nullable_model_no_key(self):
        request = self.request_generator.generate_request(command="echo_optional_multi_nullable_model",
                                                          parameters={})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_optional_multi_nullable_model_list_provided(self):
        parameters = {'param': [
            {"my_nested_string": "str1", "my_nested_int": 1}
        ]}
        request = self.request_generator.generate_request(command="echo_optional_multi_nullable_model",
                                                          parameters=parameters)
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertListEqual(parameters['param'], json.loads(response.output))

    def test_echo_optional_multi_nullable_model_with_both_defaults(self):
        request = self.request_generator.generate_request(
            command="echo_optional_multi_nullable_model_with_both_defaults")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertListEqual([{'my_foo': 'foo', 'my_bar': 'bar'}], json.loads(response.output))

    def test_echo_optional_multi_nullable_model_with_partial_default_provided(self):
        parameters = {
            'param': [
                {"my_foo": "foo_from_client"}
            ]
        }
        request = self.request_generator.generate_request(
            command="echo_optional_multi_nullable_model_with_both_defaults",
            parameters=parameters
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertListEqual([{'my_foo': 'foo_from_client', 'my_bar': 'defaultBarFromModel'}],
                             json.loads(response.output))

    def test_echo_optional_multi_nullable_model_with_model_defaults(self):
        request = self.request_generator.generate_request(
            command="echo_optional_multi_nullable_model_with_model_defaults",
            parameters={"param": [{}]}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertListEqual([{'my_foo': 'defaultFooFromModel', 'my_bar': 'defaultBarFromModel'}],
                             json.loads(response.output))

    def test_echo_optional_multi_nullable_model_with_multi_defaults(self):
        request = self.request_generator.generate_request(
            command="echo_optional_multi_nullable_model_with_multi_defaults"
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertListEqual([{'my_nested_string': 'hi', 'my_nested_int': 2}],
                             json.loads(response.output))

    def test_echo_optional_multi_nullable_model_with_multi_defaults_partial(self):
        request = self.request_generator.generate_request(
            command="echo_optional_multi_nullable_model_with_multi_defaults",
            parameters={"param": [{"my_nested_string": "hi"}]}
        )
        assert_validation_error(self, self.easy_client, request)

    def test_echo_optional_multi_nullable_string(self):
        request = self.request_generator.generate_request(command="echo_optional_multi_nullable_string")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps(["hello", "there"]))

    def test_echo_optional_multi_nullable_string_null_provided(self):
        request = self.request_generator.generate_request(command="echo_optional_multi_nullable_string",
                                                          parameters={"param": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_dictionary_no_model_invalid_type(self):
        request = self.request_generator.generate_request(command="echo_raw_dictionary",
                                                          parameters={"d": "THIS IS NOT A DICT"})
        assert_validation_error(self, self.easy_client, request)

    def test_dictionary_no_model_valid_type(self):
        request = self.request_generator.generate_request(command="echo_raw_dictionary",
                                                          parameters={"d": {"foo": "bar"}})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps({"foo": "bar"}))

    def test_echo_raw_dictionary_nullable(self):
        request = self.request_generator.generate_request(command="echo_raw_dictionary_nullable",
                                                          parameters={"d": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_raw_dictionary_nullable_no_key(self):
        request = self.request_generator.generate_request(command="echo_raw_dictionary_nullable",
                                                          parameters={})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_raw_dictionary_nullable_optional(self):
        request = self.request_generator.generate_request(command="echo_raw_dictionary_optional",
                                                          parameters={"d": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_raw_dictionary_nullable_optional_no_key(self):
        request = self.request_generator.generate_request(command="echo_raw_dictionary_optional",
                                                          parameters={})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_raw_dictionary_optional_with_default(self):
        request = self.request_generator.generate_request(command="echo_raw_dictionary_optional_with_default",
                                                          parameters={})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps({"foo": "bar"}))

    def test_echo_raw_dictionary_optional_with_maximum_too_many(self):
        request = self.request_generator.generate_request(command="echo_raw_dictionary_optional_with_maximum",
                                                          parameters={"1": "foo", "2": "foo", "3": "foo"})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_required_any_message(self):
        request = self.request_generator.generate_request(command="echo_required_any_message",
                                                          parameters={"message": {"foo": "bar"}})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output=json.dumps({"foo": "bar"}))

    def test_echo_required_any_multi_message(self):
        request = self.request_generator.generate_request(command="echo_required_any_multi_message",
                                                          parameters={"messages": [{'foo': 'bar'}]})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertListEqual([{'foo': 'bar'}], json.loads(response.output))

    def test_echo_required_message(self):
        request = self.request_generator.generate_request(command="echo_required_message")
        assert_validation_error(self, self.easy_client, request)

    def test_echo_required_message_nullable_false_no_default(self):
        request = self.request_generator.generate_request(command="echo_required_message_nullable_false_no_default")
        assert_validation_error(self, self.easy_client, request)

    def test_echo_required_message_nullable_false_with_default(self):
        request = self.request_generator.generate_request(command="echo_required_message_nullable_false_with_default",
                                                          parameters={"message": None})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_required_message_nullable_false_with_default_no_key(self):
        request = self.request_generator.generate_request(command="echo_required_message_nullable_false_with_default",
                                                          parameters={})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="cannot be null")

    def test_echo_required_message_nullable_true(self):
        request = self.request_generator.generate_request(command="echo_required_message_nullable_true",
                                                          parameters={"message": None})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_required_message_nullable_true_with_default(self):
        request = self.request_generator.generate_request(
            command="echo_required_message_nullable_true_with_non_null_default",
            parameters={"message": None}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="null")

    def test_echo_required_message_nullable_true_with_default_no_key(self):
        request = self.request_generator.generate_request(
            command="echo_required_message_nullable_true_with_non_null_default",
            parameters={}
        )
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="can be null")

    def test_echo_required_message_regex_valid(self):
        request = self.request_generator.generate_request(command="echo_required_message_regex",
                                                          parameters={"message": "Hi."})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response, output="Hi.")

    def test_echo_required_message_regex_invalid(self):
        request = self.request_generator.generate_request(command="echo_required_message_regex",
                                                          parameters={"message": "INVALID"})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_simple_model(self):
        request = self.request_generator.generate_request(command="echo_simple_model",
                                                          parameters={"model": {
                                                              "my_nested_string": "str1",
                                                              "my_nested_int": 1
                                                          }})
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertDictEqual({"my_nested_string": "str1", "my_nested_int": 1}, json.loads(response.output))

    def test_echo_simple_model_with_default(self):
        request = self.request_generator.generate_request(command="echo_simple_model_with_default")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertDictEqual({"my_nested_string": "foo", "my_nested_int": 1}, json.loads(response.output))

    def test_echo_max_value_too_high(self):
        request = self.request_generator.generate_request(command="echo_with_max_value",
                                                          parameters={"echo_max_value": 30})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_max_value_string_too_high(self):
        request = self.request_generator.generate_request(command="echo_with_max_value_string",
                                                          parameters={
                                                              "echo_max_value": "12345678901234567890123456789"
                                                          })
        assert_validation_error(self, self.easy_client, request)

    def test_echo_with_min_value_too_low(self):
        request = self.request_generator.generate_request(command="echo_with_min_value",
                                                          parameters={"echo_min_value": -1})
        assert_validation_error(self, self.easy_client, request)

    def test_echo_with_min_value_string_too_short(self):
        request = self.request_generator.generate_request(command="echo_with_min_value_string",
                                                          parameters={"echo_string": "a"})
        assert_validation_error(self, self.easy_client, request)

    def test_prove_env(self):
        request = self.request_generator.generate_request(command="prove_env")
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertDictEqual({"DB_NAME": "complex", "DB_PASS": "supersecret"}, json.loads(response.output))

    def test_weird_parameters(self):
        parameters = {
            "system": "system_value",
            "command": "command_value",
            "comment": "comment_value",
            "system_version": "system_version_value",
            "instance_name": "instance_name_value",
            "parameters": ["parameters_value"]
        }
        request = self.request_generator.generate_request(command="weird_parameter_names",
                                                          parameters=parameters)
        response = wait_for_response(self.easy_client, request)
        assert_successful_request(response)
        self.assertDictEqual(parameters, json.loads(response.output))


if __name__ == '__main__':
    unittest.main()
