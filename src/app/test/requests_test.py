# -*- coding: utf-8 -*-
import pytest
from box import Box
from brewtils.errors import ModelValidationError
from mock import Mock, call, patch

import beer_garden.requests
from beer_garden.db.mongo.models import Command, Parameter, Request, System, Choices
from beer_garden.requests import RequestValidator


@pytest.fixture
def system_find(monkeypatch):
    find_mock = Mock()
    monkeypatch.setattr(System, "find_unique", find_mock)
    return find_mock


@pytest.fixture
def validator(monkeypatch, mongo_conn):
    val = RequestValidator(
        Box({"command": {"timeout": 10}, "url": {"ca_verify": False}})
    )

    monkeypatch.setattr(beer_garden, "application", Mock(request_validator=val))

    return val


def make_param(**kwargs):
    defaults = {
        "type": "Any",
        "multi": False,
        "display_name": None,
        "optional": True,
        "default": None,
        "description": None,
        "choices": None,
        "nullable": False,
        "maximum": None,
        "minimum": None,
        "regex": None,
        "form_input_type": None,
        "parameters": [],
    }
    defaults.update(**kwargs)
    return Mock(spec=Parameter, **defaults)


def make_request(**kwargs):
    defaults = {
        "system": "s1",
        "system_version": "1",
        "instance_name": "i1",
        "command": "c1",
        "parameters": {},
    }
    defaults.update(**kwargs)
    return Mock(spec=Request, **defaults)


def _process_mock(monkeypatch, return_value=""):
    process_mock = Mock()
    process_mock.return_value.output = return_value
    monkeypatch.setattr(beer_garden.requests, "process_request", process_mock)

    return process_mock


class TestSessionConfig(object):
    def test_verify(self):
        cert_mock = Mock()
        config = Box(
            {
                "command": {"timeout": 10},
                "url": {"ca_verify": True, "ca_cert": cert_mock},
            }
        )

        assert RequestValidator(config)._session.verify == cert_mock

    def test_no_verify(self, validator):
        assert validator._session.verify is False


class TestValidateRequest(object):
    def test_success(self, validator, system_find, bg_system, bg_request):
        system_find.return_value = bg_system
        assert validator.validate_request(bg_request) == bg_request


class TestGetAndValidateSystem(object):
    def test_success(self, validator, system_find, bg_system, bg_request):
        system_find.return_value = bg_system
        assert validator.get_and_validate_system(bg_request) == bg_system

    def test_missing_system(self, validator, system_find, bg_request):
        system_find.return_value = None
        with pytest.raises(ModelValidationError):
            validator.get_and_validate_system(bg_request)

    def test_invalid_instance(self, validator, system_find, bg_system, bg_request):
        system_find.return_value = bg_system
        bg_request.instance_name = "INVALID"

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_system(bg_request)


class TestGetAndValidateCommandForSystem(object):
    def test_success(self, validator, bg_system, bg_request, bg_command):
        assert (
            validator.get_and_validate_command_for_system(bg_request, system=bg_system)
            == bg_command
        )

    def test_no_request_command(self, validator):
        with pytest.raises(ModelValidationError):
            validator.get_and_validate_command_for_system(
                Request(system="foo", parameters={}), Mock()
            )

    def test_system_lookup(
        self, monkeypatch, validator, bg_system, bg_request, bg_command
    ):
        monkeypatch.setattr(
            validator, "get_and_validate_system", Mock(return_value=bg_system)
        )
        assert validator.get_and_validate_command_for_system(bg_request) == bg_command

    def test_command_type(self, validator, bg_system, bg_request):
        bg_request.command_type = None

        validator.get_and_validate_command_for_system(bg_request, system=bg_system)
        assert bg_request.command_type == "ACTION"

    def test_output_type(self, validator, bg_system, bg_request):
        bg_request.output_type = None

        validator.get_and_validate_command_for_system(bg_request, system=bg_system)
        assert bg_request.output_type == "STRING"

    @pytest.mark.parametrize("attribute", ["command", "command_type", "output_type"])
    def test_bad_request_attributes(self, validator, bg_system, bg_request, attribute):
        setattr(bg_request, attribute, "BAD")
        with pytest.raises(ModelValidationError):
            validator.get_and_validate_command_for_system(bg_request, system=bg_system)


class TestGetAndValidateParameters(object):
    def test_success(self, validator, bg_request, bg_command):
        params = validator.get_and_validate_parameters(bg_request, command=bg_command)
        assert params == bg_request.parameters

    def test_empty(self, validator):
        req = Request(system="foo", command="command1")
        command = Command(parameters=[])
        assert validator.get_and_validate_parameters(req, command) == {}

    def test_command_lookup(self, monkeypatch, validator):
        request = Request(parameters={})
        lookup_mock = Mock(return_value=Mock(parameters=[]))
        monkeypatch.setattr(
            validator, "get_and_validate_command_for_system", lookup_mock
        )
        validator.get_and_validate_parameters(request)
        lookup_mock.assert_called_once_with(request)

    def test_bad_request_parameter_key(self, validator, bg_request, bg_command):
        bg_request.parameters = {"bad_key": "bad_value"}

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(bg_request, command=bg_command)

    def test_missing_required_key_no_default(self, validator, bg_request, bg_command):
        bg_command.parameters = [
            make_param(key="message", optional=False, default=None, nullable=False)
        ]
        bg_request.parameters = {}

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(bg_request, command=bg_command)

    def test_missing_required_key_with_default(self, validator, bg_request, bg_command):
        bg_command.parameters = [
            make_param(key="message", optional=False, default="foo", nullable=False)
        ]
        bg_request.parameters = {}

        params = validator.get_and_validate_parameters(bg_request, command=bg_command)
        assert params["message"] == "foo"

    def test_missing_nested_parameters(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": {}})
        nested_parameter = Mock(key="foo", multi=False, type="String", optional=False)
        command_parameter = Mock(
            key="key1", multi=False, type="Dictionary", parameters=[nested_parameter]
        )
        command = Mock(parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    @patch("beer_garden.requests.RequestValidator._validate_parameter_based_on_type")
    def test_extract_parameter_non_multi_calls_no_default(
        self, validate_mock, validator
    ):
        req = Request(system="foo", command="command1", parameters={"key1": "value1"})
        command_parameter = Mock(key="key1", multi=False)
        command = Mock(parameters=[command_parameter])
        validate_mock.side_effect = lambda w, x, y, z: w

        validator.get_and_validate_parameters(req, command)
        validate_mock.assert_called_once_with("value1", command_parameter, command, req)

    @patch("beer_garden.requests.RequestValidator._validate_parameter_based_on_type")
    def test_extract_parameter_non_multi_calls_with_default(
        self, validate_mock, validator
    ):
        req = Request(system="foo", command="command1", parameters={})
        command_parameter = Mock(key="key1", multi=False, default="default_value")
        command = Mock(parameters=[command_parameter])
        validate_mock.side_effect = lambda w, x, y, z: w

        validator.get_and_validate_parameters(req, command)
        validate_mock.assert_called_once_with(
            "default_value", command_parameter, command, req
        )

    @patch("beer_garden.requests.RequestValidator._validate_parameter_based_on_type")
    def test_update_and_validate_parameter_extract_parameter_multi(
        self, validate_mock, validator
    ):
        req = Request(system="foo", command="command1", parameters={"key1": [1, 2]})
        command_parameter = Mock(key="key1", multi=True)
        command = Mock(parameters=[command_parameter])
        validate_mock.side_effect = lambda w, x, y, z: w

        validator.get_and_validate_parameters(req, command)
        validate_mock.assert_has_calls(
            [
                call(1, command_parameter, command, req),
                call(2, command_parameter, command, req),
            ],
            any_order=True,
        )

    def test_update_and_validate_parameter_extract_parameter_multi_not_list(
        self, validator
    ):
        req = Request(
            system="foo", command="command1", parameters={"key1": "NOT A LIST"}
        )
        command_parameter = Mock(key="key1", multi=True)
        command = Mock(parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_update_and_validate_parameter_extract_parameter_optional_no_default(
        self, validator
    ):
        req = Request(system="foo", command="command1", parameters={})
        command_parameter = Parameter(
            key="key1", multi=False, optional=True, default=None
        )
        command = Mock(parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_update_and_validate_parameter_extract_parameter_nullable_no_default(
        self, validator
    ):
        req = Request(system="foo", command="command1", parameters={})
        command_parameter = Parameter(
            key="key1", multi=False, nullable=True, default=None
        )
        command = Mock(parameters=[command_parameter])
        validated_parameters = validator.get_and_validate_parameters(req, command)
        assert validated_parameters["key1"] is None

    def test_validate_parameter_based_on_type_null_not_nullable(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": None})
        command_parameter = Mock(key="key1", multi=False, type="String", nullable=False)
        command = Mock(parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_validate_maximum_sequence(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": "value"})

        command_parameter = Parameter(
            key="key1", multi=False, type="String", optional=False, maximum=10
        )
        command = Command("test", parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(
            key="key1", multi=False, type="String", optional=False, maximum=3
        )
        command = Command("test", parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_validate_maximum_non_sequence(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": 5})

        command_parameter = Parameter(
            key="key1", multi=False, type="Integer", optional=False, maximum=10
        )
        command = Command("test", parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(
            key="key1", multi=False, type="Integer", optional=False, maximum=3
        )
        command = Command("test", parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_validate_minimum_sequence(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": "value"})

        command_parameter = Parameter(
            key="key1", multi=False, type="String", optional=False, minimum=3
        )
        command = Command("test", parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(
            key="key1", multi=False, type="String", optional=False, minimum=10
        )
        command = Command("test", parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_validate_minimum_non_sequence(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": 5})

        command_parameter = Parameter(
            key="key1", multi=False, type="Integer", optional=False, minimum=3
        )
        command = Command("test", parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(
            key="key1", multi=False, type="Integer", optional=False, minimum=10
        )
        command = Command("test", parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_validate_regex(self, validator):
        req = Request(
            system="foo", command="command1", parameters={"key1": "Hi World!"}
        )

        command_parameter = Parameter(
            key="key1", multi=False, type="String", optional=False, regex=r"^Hi.*"
        )
        command = Command("test", parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

        command_parameter = Parameter(
            key="key1", multi=False, type="String", optional=False, regex=r"^Hello.*"
        )
        command = Command("test", parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_validate_regex_nullable(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": None})
        command_parameter = Parameter(
            key="key1", multi=False, type="String", regex=r"^Hi.*", nullable=True
        )
        command = Command("test", parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

    def test_validate_minimum_nullable(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": None})
        command_parameter = Parameter(
            key="key1",
            multi=False,
            type="Integer",
            optional=False,
            minimum=3,
            nullable=True,
        )
        command = Command("test", parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

    def test_validate_maximum_nullable(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": None})
        command_parameter = Parameter(
            key="key1",
            multi=False,
            type="Integer",
            optional=False,
            minimum=3,
            nullable=True,
        )
        command = Command("test", parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)


class TestValidateParameterType(object):
    @pytest.mark.parametrize(
        "req_value,param_type,expected",
        [
            ("1", "String", "1"),
            ("1", "Integer", 1),
            (1, "Integer", 1),
            ("1.0", "Float", 1.0),
            (1.0, "Float", 1.0),
            ({}, "Any", {}),
            ({"foo": "bar"}, "Dictionary", {"foo": "bar"}),
            (False, "Boolean", False),
            (True, "Boolean", True),
            ("1451606400000", "Date", 1451606400000),
            (1451606400000, "Date", 1451606400000),
            ("1451606400000", "Datetime", 1451606400000),
            (1451606400000, "Datetime", 1451606400000),
        ],
    )
    def test_success(self, validator, req_value, param_type, expected):
        validated_parameters = validator.get_and_validate_parameters(
            make_request(parameters={"key1": req_value}),
            Mock(parameters=[make_param(key="key1", type=param_type)]),
        )
        assert validated_parameters["key1"] == expected

    @pytest.mark.parametrize(
        "req_value,param_type",
        [
            (1, "String"),
            (1.1, "Integer"),
            ("foo", "Integer"),
            ("foo", "Boolean"),
            ("foo", "UH OH THIS IS BAD"),
            (["not an int"], "Integer"),
            ([1], "Integer"),
        ],
    )
    def test_fail(self, validator, req_value, param_type):
        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(
                make_request(parameters={"key1": req_value}),
                Mock(parameters=[make_param(key="key1", type=param_type)]),
            )

    def test_nested_parameters(self, validator):
        param = make_param(
            key="key1",
            type="Dictionary",
            parameters=[make_param(key="foo", type="String")],
        )
        validated_parameters = validator.get_and_validate_parameters(
            make_request(parameters={"key1": {"foo": "bar"}}), Mock(parameters=[param])
        )
        assert validated_parameters["key1"]["foo"] == "bar"


class TestValidateChoices(object):
    @pytest.mark.parametrize(
        "req",
        [
            make_request(parameters={"p2": "7"}),
            make_request(parameters={"p1": "a", "p2": "1"}),
        ],
    )
    def test_dictionary(self, validator, req):
        choices_value = {"a": ["1", "2", "3"], "b": ["4", "5", "6"], "null": ["7"]}

        command = Mock(
            parameters=[
                make_param(
                    key="p1",
                    choices=Mock(type="static", value=["a", "b"]),
                    nullable=True,
                ),
                make_param(
                    key="p2",
                    optional=False,
                    choices=Mock(
                        type="static",
                        value=choices_value,
                        details={"key_reference": "p1"},
                    ),
                ),
            ]
        )

        validator.get_and_validate_parameters(req, command)

    @pytest.mark.parametrize(
        "req",
        [
            make_request(parameters={"p2": "1"}),
            make_request(parameters={"p1": "a", "p2": "4"}),
            make_request(parameters={"p1": "c", "p2": "1"}),
        ],
    )
    def test_dictionary_bad_parameters(self, validator, req):
        choices_value = {"a": ["1", "2", "3"], "b": ["4", "5", "6"]}

        command = Mock(
            parameters=[
                make_param(key="p1", choices=Mock(type="static", value=["a", "b"])),
                make_param(
                    key="p2",
                    optional=False,
                    choices=Mock(
                        type="static",
                        value=choices_value,
                        details={"key_reference": "p1"},
                    ),
                ),
            ]
        )

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_invalid_parameters(self, validator):
        command = Mock(
            parameters=[
                make_param(key="p1", choices=Mock(type="static", value=["a", "b"])),
                make_param(
                    key="p2",
                    optional=False,
                    choices=Mock(type="static", value={}, details={}),
                ),
            ]
        )

        with pytest.raises(ModelValidationError):
            req = make_request(parameters={"p1": "1", "p2": "a"})
            validator.get_and_validate_parameters(req, command)

    class TestInstanceNameKey(object):
        command = Mock(
            parameters=[
                make_param(
                    key="p1",
                    optional=False,
                    choices=Mock(
                        type="static",
                        value={"i1": ["1", "2", "3"], "i2": ["4", "5", "6"]},
                        details={"key_reference": "instance_name"},
                    ),
                )
            ]
        )

        @pytest.mark.parametrize(
            "req",
            [
                make_request(instance_name="i1", parameters={"p1": "1"}),
                make_request(instance_name="i2", parameters={"p1": "4"}),
            ],
        )
        def test_success(self, validator, req):
            validator.get_and_validate_parameters(req, self.command)

        def test_failure(self, validator):
            req = make_request(instance_name="i1", parameters={"p1": "4"})

            with pytest.raises(ModelValidationError):
                validator.get_and_validate_parameters(req, self.command)

    class TestCommandParameterArgument(object):
        command = Mock(
            parameters=[
                make_param(key="p1", choices=Mock(type="static", value=["a", "b"])),
                make_param(
                    key="p2",
                    optional=False,
                    choices=Mock(type="command", value="c2(p=${p1})"),
                ),
            ]
        )

        def test_success(self, monkeypatch, validator):
            process_mock = _process_mock(monkeypatch, return_value='["1"]')
            req = make_request(parameters={"p1": "a", "p2": "1"})

            validator.get_and_validate_parameters(req, self.command)

            choices_request = process_mock.call_args[0][0]
            assert choices_request.command == "c2"
            assert choices_request.system == "s1"
            assert choices_request.system_version == "1"
            assert choices_request.instance_name == "i1"
            assert choices_request.parameters == {"p": "a"}

        def test_failure(self, monkeypatch, validator):
            _process_mock(monkeypatch, return_value='["1"]')
            req = make_request(parameters={"p1": "Fail"})

            with pytest.raises(ModelValidationError):
                validator.get_and_validate_parameters(req, self.command)

    class TestCommandInstanceNameArgument(object):
        command = Mock(
            parameters=[
                make_param(
                    key="p1",
                    optional=False,
                    choices=Mock(type="command", value="c2(p=${instance_name})"),
                )
            ]
        )

        @pytest.mark.parametrize(
            "req",
            [
                make_request(parameters={"p1": "1"}),
                make_request(instance_name="i2", parameters={"p1": "1"}),
            ],
        )
        def test_success(self, monkeypatch, validator, req):
            process_mock = _process_mock(monkeypatch, return_value='["1"]')

            validator.get_and_validate_parameters(req, self.command)

            choices_request = process_mock.call_args[0][0]
            assert choices_request.command == "c2"
            assert choices_request.system == "s1"
            assert choices_request.system_version == "1"
            assert choices_request.instance_name == req.instance_name
            assert choices_request.parameters == {"p": req.instance_name}

        def test_failure(self, monkeypatch, validator):
            _process_mock(monkeypatch, return_value='["1"]')
            req = make_request(parameters={"p1": "Fail"})

            with pytest.raises(ModelValidationError):
                validator.get_and_validate_parameters(req, self.command)

    def test_validate_value_in_choices_no_choices(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": "value"})
        command_parameter = Mock(key="key1", multi=False, type="String", choices=None)
        command = Mock(parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

    def test_validate_value_value_in_choices_not_multi_valid_choice(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": "value"})
        command_parameter = Mock(
            key="key1",
            multi=False,
            type="String",
            choices=Mock(type="static", value=["value"]),
        )
        command = Mock(parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

    def test_validate_value_in_choices_not_multi_invalid_choice(self, validator):
        req = Request(system="foo", command="command1", parameters={"key1": "value"})
        command_parameter = Mock(
            key="key1",
            multi=False,
            type="String",
            optional=False,
            choices=Mock(type="static", value=["not value"]),
        )
        command = Mock(parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_validate_value_in_choices_multi_valid_choice(self, validator):
        req = Request(
            system="foo", command="command1", parameters={"key1": ["v1", "v2"]}
        )
        command_parameter = Mock(
            key="key1",
            multi=True,
            type="String",
            choices=Mock(type="static", value=["v1", "v2"]),
        )
        command = Mock(parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

    def test_validate_value_in_choices_multi_invalid_choice(self, validator):
        req = Request(
            system="foo", command="command1", parameters={"key1": ["v1", "v2"]}
        )
        command_parameter = Mock(
            key="key1",
            multi=True,
            type="String",
            optional=False,
            choices=Mock(type="static", value=["v1", "v3"]),
        )
        command = Mock(parameters=[command_parameter])

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    def test_validate_value_in_choices_optional_none_allowed(self, validator):
        req = Request(system="foo", command="command1", parameters={})
        command_parameter = Mock(
            key="key1",
            multi=False,
            type="String",
            optional=True,
            default=None,
            choices=Mock(type="static", value=["value1", "value3"]),
        )
        command = Mock(parameters=[command_parameter])
        validator.get_and_validate_parameters(req, command)

    def test_validate_choices_static_bad_type(self, validator):
        command_parameter = Mock(
            key="key1",
            multi=False,
            type="String",
            optional=False,
            default=None,
            choices=Mock(type="static", value="bad str"),
            minimum=None,
            maximum=None,
            regex=None,
        )

        command = Mock(parameters=[command_parameter])

        req = Request(system="foo", command="command1", parameters={"key1": "1"})

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(req, command)

    @pytest.mark.parametrize(
        "response",
        [
            '[{"text": "text", "value": "value"}]',
            '[{"text": "a", "value": "b"}, {"text": "b", "value": "value"}]',
            '["value"]',
            '["a", "b", "value"]',
            '["a", {"text": "text", "value": "value"}]',
            '["a", {"text": "b", "value": "2"}, "value"]',
        ],
    )
    def test_validate_url_choices(self, validator, response):
        session_mock = Mock()
        session_mock.get.return_value.text = response
        validator._session = session_mock

        req = Request(system="foo", command="command1", parameters={"key1": "value"})
        command_parameter = Mock(
            key="key1",
            type="String",
            optional=False,
            multi=False,
            choices=Mock(type="url", value="http://localhost"),
            minimum=None,
            maximum=None,
            regex=None,
        )
        command = Mock(parameters=[command_parameter])

        validator.get_and_validate_parameters(req, command)
        session_mock.get.assert_called_with("http://localhost", params={})

    def test_validate_command_choices_dict_value(self, monkeypatch, validator):
        process_mock = _process_mock(monkeypatch, return_value='["value"]')

        request = Request(
            system="foo",
            command="command1",
            parameters={"key1": "value"},
            system_version="0.0.1",
            instance_name="instance_name",
        )
        choices_value = {
            "command": "command_name",
            "system": "foo",
            "version": "0.0.1",
            "instance_name": "default",
        }
        command = Mock(
            parameters=[
                Parameter(
                    key="key1",
                    optional=False,
                    choices=Choices(type="command", value=choices_value),
                )
            ]
        )

        validator.get_and_validate_parameters(request, command)

        choices_request = process_mock.call_args[0][0]
        assert choices_request.command == "command_name"
        assert choices_request.system == "foo"
        assert choices_request.system_version == "0.0.1"
        assert choices_request.instance_name == "default"

    def test_validate_command_choices_bad_value_type(self, monkeypatch, validator):
        _process_mock(monkeypatch, return_value='["value"]')

        request = Request(
            system="foo",
            command="command1",
            parameters={"key1": "value"},
            system_version="0.0.1",
            instance_name="instance_name",
        )
        command = Mock(
            parameters=[
                Parameter(
                    key="key1", optional=False, choices=Choices(type="command", value=1)
                )
            ]
        )

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(request, command)

    def test_validate_command_choices_simple_list_response(
        self, monkeypatch, validator
    ):
        process_mock = _process_mock(monkeypatch, return_value='["value"]')

        request = Request(
            system="foo",
            command="command1",
            parameters={"key1": "value"},
            system_version="0.0.1",
            instance_name="instance_name",
        )
        command = Mock(
            parameters=[
                Parameter(
                    key="key1",
                    choices=Choices(type="command", value="command_name"),
                    optional=False,
                )
            ]
        )

        validator.get_and_validate_parameters(request, command)

        choices_request = process_mock.call_args[0][0]
        assert choices_request.command == "command_name"
        assert choices_request.system == "foo"
        assert choices_request.system_version == "0.0.1"
        assert choices_request.instance_name == "instance_name"

    def test_validate_command_choices_dictionary_list_response(
        self, monkeypatch, validator
    ):
        process_mock = _process_mock(monkeypatch, return_value='[{"value": "value"}]')

        request = Request(
            system="foo",
            command="command1",
            parameters={"key1": "value"},
            system_version="0.0.1",
            instance_name="instance_name",
        )
        command = Mock(
            parameters=[
                Parameter(
                    key="key1",
                    choices=Choices(type="command", value="command_name"),
                    optional=False,
                )
            ]
        )

        validator.get_and_validate_parameters(request, command)

        choices_request = process_mock.call_args[0][0]
        assert choices_request.command == "command_name"
        assert choices_request.system == "foo"
        assert choices_request.system_version == "0.0.1"
        assert choices_request.instance_name == "instance_name"

    def test_validate_command_choices_bad_parameter(self, monkeypatch, validator):
        _process_mock(monkeypatch, return_value='{"value": "value"}')

        request = Request(
            system="foo",
            command="command1",
            parameters={"key1": "value"},
            system_version="0.0.1",
            instance_name="instance_name",
        )
        command = Mock(
            parameters=[
                Parameter(
                    key="key1",
                    choices=Choices(type="foo", value="command_name"),
                    optional=False,
                )
            ]
        )

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(request, command)

    def test_validate_command_choices_empty_list_output(self, monkeypatch, validator):
        _process_mock(monkeypatch, return_value="[]")

        request = Request(
            system="foo",
            command="command1",
            parameters={"key1": "value"},
            system_version="0.0.1",
            instance_name="instance_name",
        )
        command = Mock(
            parameters=[
                Parameter(
                    key="key1",
                    choices=Choices(type="command", value="command_name"),
                    optional=False,
                )
            ]
        )

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(request, command)

    def test_validate_command_choices_bad_output_type(self, monkeypatch, validator):
        _process_mock(monkeypatch, return_value='{"value": "value"}')

        request = Request(
            system="foo",
            command="command1",
            parameters={"key1": "value"},
            system_version="0.0.1",
            instance_name="instance_name",
        )
        command = Mock(
            parameters=[
                Parameter(
                    key="key1",
                    choices=Choices(type="command", value="command_name"),
                    optional=False,
                )
            ]
        )

        with pytest.raises(ModelValidationError):
            validator.get_and_validate_parameters(request, command)
