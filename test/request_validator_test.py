import unittest

from mock import MagicMock, Mock, call, patch, PropertyMock

from bartender.request_validator import RequestValidator
from bg_utils.models import Command, Instance, Parameter, Request, System, Choices
from brewtils.errors import ModelValidationError


class RequestTest(unittest.TestCase):

    def setUp(self):
        config = MagicMock(web_host='web_host', web_port=123, ca_verify=False, ssl_enabled=False,
                           url_prefix=None, ca_cert=None)
        self.validator = RequestValidator(config)

    @patch('bg_utils.models.System.find_unique', Mock(return_value=None))
    def test_get_and_validate_system_no_system(self):
        req = Request(system='foo', command='bar', parameters={})
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_system, req)

    @patch('bg_utils.models.System.find_unique')
    def test_get_and_validate_system_with_system(self, find_mock):
        system = System(name="foo", instances=[Instance(name="default")])
        find_mock.return_value = system
        req = Request(system='foo', command='bar', instance_name="default", parameters={})
        self.assertEqual(self.validator.get_and_validate_system(req), system)

    @patch('bg_utils.models.System.find_unique')
    def test_get_and_validate_system_invalid_instance_name(self, find_mock):
        system = System(name="foo", instances=[Instance(name="instance1")])
        find_mock.return_value = system
        req = Request(system='foo', command='bar', instance_name='INVALID', parameters={})
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_system, req)

    def test_get_and_validate_command_none_provided(self):
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_command_for_system,
                          Request(system='foo', parameters={}), Mock())

    def test_get_and_validate_command_good_command(self):
        mock_name = PropertyMock(return_value='command1')
        command = Mock(command_type='ACTION', output_type='STRING')
        type(command).name = mock_name
        system = Mock(commands=[command])
        req = Request(system='foo', command='command1', parameters={})
        self.assertEqual(self.validator.get_and_validate_command_for_system(req, system), command)

    @patch('bartender.request_validator.RequestValidator.get_and_validate_system')
    def test_get_and_validate_command_no_system_passed_in(self, mock_get):
        mock_name = PropertyMock(return_value='command1')
        command = Mock(command_type='ACTION', output_type='STRING')
        type(command).name = mock_name
        system = Mock(commands=[command])
        mock_get.return_value = system
        req = Request(system='foo', command='command1', parameters={})
        self.assertEqual(self.validator.get_and_validate_command_for_system(req), command)

    def test_get_and_validate_command_not_found(self):
        mock_name = PropertyMock(return_value='command1')
        command = Mock()
        type(command).name = mock_name
        system = Mock(commands=[command])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_command_for_system,
                          Request(system='foo', command='command2', parameters={}), system)

    def test_get_and_validate_command_no_command_type_specified(self):
        mock_name = PropertyMock(return_value='command1')
        command = Mock(command_type='ACTION', output_type='STRING')
        type(command).name = mock_name
        system = Mock(commands=[command])
        req = Request(system='foo', command='command1', parameters={}, command_type=None)
        self.validator.get_and_validate_command_for_system(req, system)
        self.assertEqual(req.command_type, 'ACTION')

    def test_get_and_validate_command_for_system_bad_command_type(self):
        mock_name = PropertyMock(return_value='command1')
        command = Mock()
        type(command).name = mock_name
        system = Mock(commands=[command])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_command_for_system,
                          Request(system='foo', command='command1', parameters={},
                                  command_type='BAD'), system)

    def test_get_and_validate_command_no_output_type_specified(self):
        mock_name = PropertyMock(return_value='command1')
        command = Mock(output_type='STRING', command_type='ACTION')
        type(command).name = mock_name
        system = Mock(commands=[command])
        req = Request(system='foo', command='command1', parameters={}, output_type=None)
        self.validator.get_and_validate_command_for_system(req, system)
        self.assertEqual(req.output_type, 'STRING')

    def test_get_and_validate_command_for_system_bad_output_type(self):
        mock_name = PropertyMock(return_value='command1')
        command = Mock()
        type(command).name = mock_name
        system = Mock(commands=[command])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_command_for_system,
                          Request(system='foo', command='command1', parameters={},
                                  output_type='BAD'), system)

    def test_get_and_validate_parameters_empty_parameters(self):
        req = Request(system='foo', command='command1')
        command = Mock(parameters=[])
        self.assertEqual(self.validator.get_and_validate_parameters(req, command), {})

    @patch('bartender.request_validator.RequestValidator.get_and_validate_command_for_system')
    def test_get_and_validate_parameters_no_command(self, get_mock):
        req = Request(system='foo', command='command1', parameters={})
        get_mock.return_value = Mock(parameters=[])
        self.validator.get_and_validate_parameters(req)
        get_mock.assert_called_with(req)

    def test_get_and_validate_parameters_bad_key_in_request_parameters(self):
        req = Request(system='foo', command='command1', parameters={'bad_key': 'bad_value'})
        command = Mock(parameters=[])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_get_and_validate_parameters_for_command_required_key_not_provided(self):
        mock_name = PropertyMock(return_value='command1')
        req = Request(system='foo', command='command1')
        command = Mock()
        type(command).name = mock_name
        command.parameters = [Mock(key='key1', optional=False, default=None, nullable=False)]
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_get_and_validate_parameters_for_command_with_nested_parameters_not_provided(self):
        req = Request(system='foo', command='command1', parameters={'key1': {}})
        nested_parameter = Mock(key="foo", multi=False, type="String", optional=False)
        command_parameter = Mock(key="key1", multi=False, type="Dictionary",
                                 parameters=[nested_parameter])
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_get_and_validate_parameters_required_key_not_provided_but_default_provided(self):
        req = Request(system='foo', command='command1')
        command = Mock(parameters=[Parameter(key="key1", optional=False, default="value1")])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertEqual(validated_parameters['key1'], 'value1')

    @patch('bartender.request_validator.RequestValidator._validate_parameter_based_on_type')
    def test_extract_parameter_non_multi_calls_no_default(self, validate_mock):
        req = Request(system='foo', command='command1', parameters={'key1': 'value1'})
        command_parameter = Mock(key="key1", multi=False)
        command = Mock(parameters=[command_parameter])
        validate_mock.side_effect = lambda w, x, y, z: w

        self.validator.get_and_validate_parameters(req, command)
        validate_mock.assert_called_once_with('value1', command_parameter, command, req)

    @patch('bartender.request_validator.RequestValidator._validate_parameter_based_on_type')
    def test_extract_parameter_non_multi_calls_with_default(self, validate_mock):
        req = Request(system='foo', command='command1', parameters={})
        command_parameter = Mock(key="key1", multi=False, default="default_value")
        command = Mock(parameters=[command_parameter])
        validate_mock.side_effect = lambda w, x, y, z: w

        self.validator.get_and_validate_parameters(req, command)
        validate_mock.assert_called_once_with('default_value', command_parameter, command, req)

    @patch('bartender.request_validator.RequestValidator._validate_parameter_based_on_type')
    def test_update_and_validate_parameter_extract_parameter_multi_calls(self, validate_mock):
        req = Request(system='foo', command='command1', parameters={"key1": [1, 2]})
        command_parameter = Mock(key="key1", multi=True)
        command = Mock(parameters=[command_parameter])
        validate_mock.side_effect = lambda w, x, y, z: w

        self.validator.get_and_validate_parameters(req, command)
        validate_mock.assert_has_calls([call(1, command_parameter, command, req),
                                        call(2, command_parameter, command, req)], any_order=True)

    def test_update_and_validate_parameter_extract_parameter_multi_not_list(self):
        req = Request(system='foo', command='command1', parameters={"key1": 'NOT A LIST'})
        command_parameter = Mock(key="key1", multi=True)
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_update_and_validate_parameter_extract_parameter_optional_and_no_default(self):
        req = Request(system='foo', command='command1', parameters={})
        command_parameter = Parameter(key="key1", multi=False, optional=True, default=None)
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_update_and_validate_parameter_extract_parameter_nullable_and_no_default(self):
        req = Request(system='foo', command='command1', parameters={})
        command_parameter = Parameter(key="key1", multi=False, nullable=True, default=None)
        command = Mock(parameters=[command_parameter])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertIsNone(validated_parameters['key1'])

    def test_validate_parameter_based_on_type_null_not_nullable(self):
        req = Request(system='foo', command='command1', parameters={'key1': None})
        command_parameter = Mock(key="key1", multi=False, type="String", nullable=False)
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_parameter_based_on_type_good_string(self):
        req = Request(system='foo', command='command1', parameters={'key1': "1"})
        command_parameter = Mock(key="key1", multi=False, type="String")
        command = Mock(parameters=[command_parameter])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertEqual(validated_parameters["key1"], "1")

    def test_validate_parameter_based_on_type_bad_string(self):
        req = Request(system='foo', command='command1', parameters={'key1': 1})
        command_parameter = Mock(key="key1", multi=False, type="String")
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_parameter_based_on_type_good_integer(self):
        req = Request(system='foo', command='command1', parameters={'key1': 1})
        command_parameter = Mock(key="key1", multi=False, type="Integer")
        command = Mock(parameters=[command_parameter])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertEqual(validated_parameters['key1'], 1)

    def test_validate_parameter_based_on_type_bad_integer(self):
        req = Request(system='foo', command='command1', parameters={'key1': 1.1})
        command_parameter = Mock(key="key1", multi=False, type="Integer")
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_parameter_based_on_type_good_float(self):
        req = Request(system='foo', command='command1', parameters={'key1': 1.0})
        command_parameter = Mock(key="key1", multi=False, type="Float")
        command = Mock(parameters=[command_parameter])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertEqual(validated_parameters['key1'], 1.0)

    def test_validate_parameter_based_on_type_good_any(self):
        req = Request(system='foo', command='command1', parameters={'key1': {}})
        command_parameter = Mock(key="key1", multi=False, type="Any")
        command = Mock(parameters=[command_parameter])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertEqual(validated_parameters['key1'], {})

    def test_validate_parameter_based_on_type_good_boolean_false(self):
        req = Request(system='foo', command='command1', parameters={'key1': False})
        command_parameter = Mock(key="key1", multi=False, type="Boolean")
        command = Mock(parameters=[command_parameter])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertFalse(validated_parameters["key1"])

    def test_validate_parameter_based_on_type_good_boolean_true(self):
        req = Request(system='foo', command='command1', parameters={'key1': True})
        command_parameter = Mock(key="key1", multi=False, type="Boolean")
        command = Mock(parameters=[command_parameter])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertTrue(validated_parameters["key1"])

    def test_validate_parameter_based_on_type_invalid_boolean(self):
        req = Request(system='foo', command='command1', parameters={'key1': "not true or false"})
        command_parameter = Mock(key="key1", multi=False, type="Boolean")
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_parameter_based_on_type_good_dictionary(self):
        req = Request(system='foo', command='command1', parameters={'key1': {'foo': 'bar'}})
        command_parameter = Mock(key="key1", multi=False, type="Dictionary", parameters=None)
        command = Mock(parameters=[command_parameter])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertEqual(validated_parameters['key1'], {'foo': 'bar'})

    def test_validate_parameter_based_on_type_with_nested_parameters(self):
        req = Request(system='foo', command='command1', parameters={'key1': {'foo': 'bar'}})
        nested_parameter = Mock(key="foo", multi=False, type="String")
        command_parameter = Mock(key="key1", multi=False, type="Dictionary",
                                 parameters=[nested_parameter])
        command = Mock(parameters=[command_parameter])
        validated_parameters = self.validator.get_and_validate_parameters(req, command)
        self.assertEqual(validated_parameters['key1']['foo'], 'bar')

    def test_validate_parameter_based_on_type_invalid_type(self):
        req = Request(system='foo', command='command1', parameters={'key1': {'foo': 'bar'}})
        command_parameter = Mock(key="key1", multi=False, type="UH OH THIS IS BAD")
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_parameter_based_on_type_type_conversion_error(self):
        req = Request(system='foo', command='command1', parameters={'key1': ["this isnt a int"]})
        command_parameter = Mock(key="key1", multi=False, type="Integer")
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_parameter_based_on_type_value_conversion_error(self):
        req = Request(system='foo', command='command1', parameters={'key1': "this isn't an int"})
        command_parameter = Mock(key="key1", multi=False, type="Integer")
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_value_in_choices_no_choices(self):
        req = Request(system='foo', command='command1', parameters={'key1': 'value'})
        command_parameter = Mock(key='key1', multi=False, type='String', choices=None)
        command = Mock(parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

    def test_validate_value_value_in_choices_not_multi_valid_choice(self):
        req = Request(system='foo', command='command1', parameters={'key1': 'value'})
        command_parameter = Mock(key='key1', multi=False, type='String',
                                 choices=Mock(type='static', value=['value']))
        command = Mock(parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

    def test_validate_value_in_choices_not_multi_invalid_choice(self):
        req = Request(system='foo', command='command1', parameters={'key1': 'value'})
        command_parameter = Mock(key='key1', multi=False, type='String', optional=False,
                                 choices=Mock(type='static', value=['not value']))
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_value_in_choices_multi_valid_choice(self):
        req = Request(system='foo', command='command1', parameters={'key1': ['v1', 'v2']})
        command_parameter = Mock(key='key1', multi=True, type='String',
                                 choices=Mock(type='static', value=['v1', 'v2']))
        command = Mock(parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

    def test_validate_value_in_choices_multi_invalid_choice(self):
        req = Request(system='foo', command='command1', parameters={'key1': ['v1', 'v2']})
        command_parameter = Mock(key='key1', multi=True, type='String', optional=False,
                                 choices=Mock(type='static', value=['v1', 'v3']))
        command = Mock(parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_value_in_choices_optional_none_allowed(self):
        req = Request(system='foo', command='command1', parameters={})
        command_parameter = Mock(key='key1', multi=False, type='String', optional=True,
                                 default=None,
                                 choices=Mock(type='static', value=['value1', 'value3']))
        command = Mock(parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

    def test_validate_choices_static_dictionary_with_key_reference(self):
        choices_value = {'a': ['1', '2', '3'], 'b': ['4', '5', '6']}

        command_parameter_1 = Mock(key='key1', multi=False, type='String', optional=False,
                                   default=None,
                                   choices=Mock(type='static', value=choices_value,
                                                details={'key_reference': 'key2'}),
                                   minimum=None, maximum=None, regex=None)
        command_parameter_2 = Mock(key='key2', multi=False, type='String', optional=False,
                                   default=None,
                                   choices=Mock(type='static', value=['a', 'b']),
                                   minimum=None, maximum=None,
                                   regex=None)
        command = Mock(parameters=[command_parameter_1, command_parameter_2])

        good_req = Request(system='foo', command='command1', parameters={'key1': '1', 'key2': 'a'})
        bad_req = Request(system='foo', command='command1', parameters={'key1': '4', 'key2': 'a'})

        self.validator.get_and_validate_parameters(good_req, command)
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, bad_req, command)

    def test_validate_choices_static_dictionary_no_key_reference(self):
        choices_value = {'a': ['1', '2', '3'], 'b': ['4', '5', '6']}

        command_parameter_1 = Mock(key='key1', multi=False, type='String', optional=False,
                                   default=None,
                                   choices=Mock(type='static', value=choices_value, details={}),
                                   minimum=None, maximum=None, regex=None)
        command_parameter_2 = Mock(key='key2', multi=False, type='String', optional=False,
                                   default=None,
                                   choices=Mock(type='static', value=['a', 'b']), minimum=None,
                                   maximum=None,
                                   regex=None)
        command = Mock(parameters=[command_parameter_1, command_parameter_2])

        req = Request(system='foo', command='command1', parameters={'key1': '1', 'key2': 'a'})

        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_choicesno_key_reference_parameter_in_request_null_in_choices(self):
        choices_value = {'a': ['1', '2', '3'], 'b': ['4', '5', '6'], 'null': ['1']}

        command_parameter_1 = Mock(key='key1', multi=False, type='String', optional=False,
                                   default=None,
                                   choices=Mock(type='static', value=choices_value,
                                                details={'key_reference': 'key2'}),
                                   minimum=None, maximum=None, regex=None)
        command_parameter_2 = Mock(key='key2', multi=False, type='String', optional=True,
                                   default=None, nullable=True,
                                   choices=Mock(type='static', value=['a', 'b']),
                                   minimum=None, maximum=None,
                                   regex=None)
        command = Mock(parameters=[command_parameter_1, command_parameter_2])

        req = Request(system='foo', command='command1', parameters={'key1': '1'})

        self.validator.get_and_validate_parameters(req, command)

    def test_validate_choices_no_key_reference_parameter_in_request_no_null_in_choices(self):
        choices_value = {'a': ['1', '2', '3'], 'b': ['4', '5', '6']}

        command_parameter_1 = Mock(key='key1', multi=False, type='String', optional=False,
                                   default=None,
                                   choices=Mock(type='static', value=choices_value,
                                                details={'key_reference': 'key2'}),
                                   minimum=None, maximum=None, regex=None)
        command_parameter_2 = Mock(key='key2', multi=False, type='String', optional=False,
                                   default=None,
                                   choices=Mock(type='static', value=['a', 'b']),
                                   minimum=None, maximum=None,
                                   regex=None)
        command = Mock(parameters=[command_parameter_1, command_parameter_2])

        req = Request(system='foo', command='command1', parameters={'key1': '1'})

        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_choices_static_dictionary_invalid_key_reference(self):
        choices_value = {'a': ['1', '2', '3'], 'b': ['4', '5', '6']}

        command_parameter_1 = Mock(key='key1', multi=False, type='String', optional=False,
                                   default=None,
                                   choices=Mock(type='static', value=choices_value,
                                                details={'key_reference': 'key2'}),
                                   minimum=None, maximum=None, regex=None)
        command_parameter_2 = Mock(key='key2', multi=False, type='String', optional=False,
                                   default=None,
                                   choices=Mock(type='static', value=['a', 'b']),
                                   minimum=None, maximum=None,
                                   regex=None)
        command = Mock(parameters=[command_parameter_1, command_parameter_2])

        req = Request(system='foo', command='command1', parameters={'key1': '1', 'key2': 'c'})

        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_choices_static_bad_type(self):
        command_parameter = Mock(key='key1', multi=False, type='String', optional=False,
                                 default=None,
                                 choices=Mock(type='static', value='bad str'), minimum=None,
                                 maximum=None, regex=None)

        command = Mock(parameters=[command_parameter])

        req = Request(system='foo', command='command1', parameters={'key1': '1'})

        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_url_choices(self):
        session_mock = Mock()
        session_mock.get.return_value.text = '[{"value": "value"}]'
        self.validator._session = session_mock

        req = Request(system='foo', command='command1', parameters={'key1': 'value'})
        command_parameter = Mock(key='key1', type='String', optional=False, multi=False,
                                 choices=Mock(type='url', value='http://localhost'),
                                 minimum=None, maximum=None,
                                 regex=None)
        command = Mock(parameters=[command_parameter])

        self.validator.get_and_validate_parameters(req, command)
        session_mock.get.assert_called_with('http://localhost', params={})

    def test_validate_command_choices_dict_value(self):
        mock_client = Mock()
        mock_client.send_bg_request.return_value.output = '["value"]'
        self.validator._client = mock_client

        request = Request(system='foo', command='command1', parameters={'key1': 'value'},
                          system_version='0.0.1', instance_name='instance_name')
        choices_value = {'command': 'command_name', 'system': 'foo', 'version': '0.0.1',
                         'instance_name': 'default'}
        command = Mock(parameters=[Parameter(key='key1', optional=False,
                                             choices=Choices(type='command', value=choices_value))])

        self.validator.get_and_validate_parameters(request, command)
        mock_client.send_bg_request.assert_called_with(_command='command_name', _system_name='foo',
                                                       _system_version='0.0.1',
                                                       _instance_name='default')

    def test_validate_command_choices_bad_value_type(self):
        mock_client = Mock()
        mock_client.send_bg_request.return_value.output = '["value"]'
        self.validator._client = mock_client

        request = Request(system='foo', command='command1', parameters={'key1': 'value'},
                          system_version='0.0.1', instance_name='instance_name')
        command = Mock(parameters=[Parameter(key='key1', optional=False,
                                             choices=Choices(type='command', value=1))])

        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, request, command)

    def test_validate_command_choices_simple_list_response(self):
        mock_client = Mock()
        mock_client.send_bg_request.return_value.output = '["value"]'
        self.validator._client = mock_client

        request = Request(system='foo', command='command1', parameters={'key1': 'value'},
                          system_version='0.0.1', instance_name='instance_name')
        command = Mock(parameters=[Parameter(key='key1', choices=Choices(type='command',
                                                                         value='command_name'),
                                             optional=False)])

        self.validator.get_and_validate_parameters(request, command)
        mock_client.send_bg_request.assert_called_with(_command='command_name', _system_name='foo',
                                                       _system_version='0.0.1',
                                                       _instance_name='instance_name')

    def test_validate_command_choices_dictionary_list_response(self):
        mock_client = Mock()
        mock_client.send_bg_request.return_value.output = '[{"value": "value"}]'
        self.validator._client = mock_client

        request = Request(system='foo', command='command1', parameters={'key1': 'value'},
                          system_version='0.0.1', instance_name='instance_name')
        command = Mock(parameters=[Parameter(key='key1', choices=Choices(type='command',
                                                                         value='command_name'),
                                             optional=False)])

        self.validator.get_and_validate_parameters(request, command)
        mock_client.send_bg_request.assert_called_with(_command='command_name', _system_name='foo',
                                                       _system_version='0.0.1',
                                                       _instance_name='instance_name')

    def test_validate_command_choices_bad_parameter(self):
        mock_client = Mock()
        mock_client.send_bg_request.return_value.output = '{"value": "value"}'
        self.validator._client = mock_client

        request = Request(system='foo', command='command1', parameters={'key1': 'value'},
                          system_version='0.0.1', instance_name='instance_name')
        command = Mock(parameters=[Parameter(key='key1', choices=Choices(type='foo',
                                                                         value='command_name'),
                                             optional=False)])

        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, request, command)

    def test_validate_command_choices_empty_list_output(self):
        mock_client = Mock()
        mock_client.send_bg_request.return_value = Mock(output='[]')
        self.validator._client = mock_client

        request = Request(system='foo', command='command1', parameters={'key1': 'value'},
                          system_version='0.0.1', instance_name='instance_name')
        command = Mock(parameters=[Parameter(key='key1', choices=Choices(type='command',
                                                                         value='command_name'),
                                             optional=False)])

        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, request, command)

    def test_validate_command_choices_bad_output_type(self):
        mock_client = Mock()
        mock_client.send_bg_request.return_value = Mock(output='{"value": "value"}')
        self.validator._client = mock_client

        request = Request(system='foo', command='command1', parameters={'key1': 'value'},
                          system_version='0.0.1', instance_name='instance_name')
        command = Mock(parameters=[Parameter(key='key1', choices=Choices(type='command',
                                                                         value='command_name'),
                                             optional=False)])

        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, request, command)

    def test_validate_maximum_sequence(self):
        req = Request(system='foo', command='command1', parameters={'key1': 'value'})

        command_parameter = Parameter(key='key1', multi=False, type='String', optional=False,
                                      maximum=10)
        command = Command('test', parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(key='key1', multi=False, type='String', optional=False,
                                      maximum=3)
        command = Command('test', parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_maximum_non_sequence(self):
        req = Request(system='foo', command='command1', parameters={'key1': 5})

        command_parameter = Parameter(key='key1', multi=False, type='Integer', optional=False,
                                      maximum=10)
        command = Command('test', parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(key='key1', multi=False, type='Integer', optional=False,
                                      maximum=3)
        command = Command('test', parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_minimum_sequence(self):
        req = Request(system='foo', command='command1', parameters={'key1': 'value'})

        command_parameter = Parameter(key='key1', multi=False, type='String', optional=False,
                                      minimum=3)
        command = Command('test', parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(key='key1', multi=False, type='String', optional=False,
                                      minimum=10)
        command = Command('test', parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_minimum_non_sequence(self):
        req = Request(system='foo', command='command1', parameters={'key1': 5})

        command_parameter = Parameter(key='key1', multi=False, type='Integer', optional=False,
                                      minimum=3)
        command = Command('test', parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(key='key1', multi=False, type='Integer', optional=False,
                                      minimum=10)
        command = Command('test', parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_regex(self):
        req = Request(system='foo', command='command1', parameters={'key1': 'Hi World!'})

        command_parameter = Parameter(key='key1', multi=False, type='String', optional=False,
                                      regex=r'^Hi.*')
        command = Command('test', parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(key='key1', multi=False, type='String', optional=False,
                                      regex=r'^Hello.*')
        command = Command('test', parameters=[command_parameter])
        self.assertRaises(ModelValidationError,
                          self.validator.get_and_validate_parameters, req, command)

    def test_validate_regex_nullable(self):
        req = Request(system='foo', command='command1', parameters={'key1': None})
        command_parameter = Parameter(key='key1', multi=False, type='String', regex=r'^Hi.*',
                                      nullable=True)
        command = Command('test', parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

    def test_validate_minimum_nullable(self):
        req = Request(system='foo', command='command1', parameters={'key1': None})
        command_parameter = Parameter(key='key1', multi=False, type='Integer', optional=False,
                                      minimum=3, nullable=True)
        command = Command('test', parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)

    def test_validate_maximum_nullable(self):
        req = Request(system='foo', command='command1', parameters={'key1': None})
        command_parameter = Parameter(key='key1', multi=False, type='Integer', optional=False,
                                      minimum=3, nullable=True)
        command = Command('test', parameters=[command_parameter])
        self.validator.get_and_validate_parameters(req, command)
