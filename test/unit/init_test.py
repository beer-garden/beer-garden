from __future__ import unicode_literals

import os
from io import open

import pytest
from box import Box
from mock import patch, MagicMock, Mock
from pymongo.errors import ServerSelectionTimeoutError
from yapconf import YapconfSpec

import bg_utils


@pytest.fixture
def spec():
    return YapconfSpec({
        'log_config': {'required': False, 'default': None},
        'log_file': {'required': False, 'default': None},
        'log_level': {'required': False, 'default': 'INFO'},
        'configuration': {
            'type': 'dict',
            'bootstrap': True,
            'items': {
                'file': {
                    'required': False,
                    'bootstrap': True,
                    'cli_short_name': 'c'
                },
                'type': {
                    'required': False,
                    'bootstrap': True,
                    'cli_short_name': 't'
                },
            },
        },
    })


class TestBgUtils(object):

    def test_parse_args(self, spec):
        cli_args = ["--log-config", "/path/to/log/config",
                    "--log-file", "/path/to/log/file",
                    "--log-level", "INFO"]
        args = bg_utils.parse_args(spec, ['log_config', 'log_file', 'log_level'], cli_args)
        assert args.log_config == "/path/to/log/config"
        assert args.log_level == "INFO"
        assert args.log_file == "/path/to/log/file"

    def test_generate_config(self, spec):
        config = bg_utils._generate_config(spec, ["-c", "/path/to/config"])
        assert config.log_file is None
        assert config.log_config is None
        assert config.log_level == 'INFO'
        assert config.configuration.file == '/path/to/config'

    @pytest.mark.parametrize('file_type', ['json', 'yaml'])
    def test_generate_config_file(self, spec, tmpdir, file_type):
        filename = os.path.join(str(tmpdir), 'temp.'+file_type)
        bg_utils.generate_config_file(spec, ['-c', filename, '-t', file_type])

        # For this case we don't tell generate the file type
        filename2 = os.path.join(str(tmpdir), 'temp2.'+file_type)
        bg_utils.generate_config_file(spec, ['-c', filename2])

        assert os.path.getsize(filename) > 0
        assert os.path.getsize(filename2) > 0

    @pytest.mark.parametrize('file_type', ['json', 'yaml'])
    def test_generate_config_file_print(self, spec, capsys, file_type):
        bg_utils.generate_config_file(spec, ['-t', file_type])

        # Just make sure we printed something
        assert capsys.readouterr().out

    @pytest.mark.parametrize('file_type', ['json', 'yaml'])
    def test_update_config(self, spec, file_type):
        spec.update_defaults = Mock()
        spec.migrate_config_file = Mock()
        bg_utils.update_config_file(spec, ["-c", "/path/to/config."+file_type])

        expected = Box({"log_file": None, "log_level": "INFO", "log_config": None,
                        "configuration": {"file": "/path/to/config."+file_type}})
        spec.migrate_config_file.assert_called_once_with(expected.configuration.file,
                                                         update_defaults=True,
                                                         current_file_type=file_type,
                                                         output_file_type=file_type)

    def test_update_config_no_config_specified(self, spec):
        spec.migrate_config_file = Mock()
        with pytest.raises(SystemExit):
            bg_utils.update_config_file(spec, [])

        assert spec.migrate_config_file.called is False

    @patch('bg_utils.open')
    def test_generate_logging_config(self, open_mock, spec):
        fake_file = Mock()
        fake_file.__exit__ = Mock()
        fake_file.__enter__ = Mock(return_value=fake_file)
        open_mock.return_value = fake_file
        generated_config = {'foo': 'bar'}
        config_generator = Mock(return_value=generated_config)

        logging_config = bg_utils.generate_logging_config_file(
            spec, config_generator, ["--log-config", "/path/to/log/config"])
        assert logging_config == generated_config
        assert open_mock.called is True

    @patch('bg_utils.open')
    def test_generate_logging_config_no_file(self, open_mock, spec):
        generated_config = {'foo': 'bar'}
        config_generator = Mock(return_value=generated_config)

        logging_config = bg_utils.generate_logging_config_file(spec, config_generator, [])
        config_generator.assert_called_with('INFO', None)
        assert logging_config == generated_config
        assert open_mock.called is False

    @pytest.mark.parametrize('config', [
        # (file extension, file type, file contents)
        ('yaml', 'yaml', 'log_level: DEBUG'),
        ('yaml', None, 'log_level: DEBUG'),
        ('json', None, '{"log_level": "DEBUG"}'),
        ('json', 'json', '{"log_level": "DEBUG"}'),
        ('', 'yaml', 'log_level: DEBUG'),
        ('', None, 'log_level: DEBUG'),
    ])
    def test_setup_with_config_file(self, tmpdir, spec, config):

        config_file = os.path.join(str(tmpdir), 'config.'+config[0])
        cli_args = {'configuration': {'file': config_file, 'type': config[1]}}

        with open(config_file, 'w') as f:
            f.write(config[2])

        generated_config = bg_utils.load_application_config(spec, cli_args)
        assert generated_config.log_level == 'DEBUG'

    def test_load_application_config_no_file_given(self, spec):
        config = bg_utils.load_application_config(spec, {})
        assert type(config) == Box

    @patch('bg_utils.logging.config.dictConfig')
    def test_setup_application_logging_no_log_config(self, config_mock):
        app_config = Box({'log': {'config_file': None}})
        bg_utils.setup_application_logging(app_config, {})
        config_mock.assert_called_with({})

    @patch('bg_utils.open')
    @patch('json.load')
    @patch('bg_utils.logging.config.dictConfig')
    def test_setup_application_logging_from_file(self, config_mock, json_mock, open_mock):
        fake_file = Mock()
        fake_file.__exit__ = Mock()
        fake_file.__enter__ = Mock(return_value=fake_file)
        open_mock.return_value = fake_file
        fake_config = {"foo": "bar"}
        json_mock.return_value = fake_config
        app_config = Mock(log_config="/path/to/log/config")
        bg_utils.setup_application_logging(app_config, {})
        config_mock.assert_called_with({'foo': 'bar'})

    def test_generate_logging_config_no_mock(self, tmpdir, spec):
        config_path = tmpdir.join('logging-config.json')
        generated_config = {'foo': 'bar'}
        config_generator = Mock(return_value=generated_config)

        logging_config = bg_utils.generate_logging_config_file(
            spec, config_generator, ['--log-config', str(config_path)])

        assert logging_config == generated_config

    @patch('mongoengine.register_connection')
    @patch('mongoengine.connect')
    @patch('bg_utils._verify_db')
    def test_setup_database_connect(self, verify_mock, connect_mock, register_mock):
        app_config = Box({
            'db': {
                'name': 'db_name',
                'connection': {
                    'username': 'db_username',
                    'password': 'db_password',
                    'host': 'db_host',
                    'port': 'db_port',
                },
            },
        })
        assert bg_utils.setup_database(app_config) is True
        connect_mock.assert_called_with(alias='aliveness', db='db_name',
                                        username='db_username',
                                        password='db_password',
                                        host='db_host', port='db_port',
                                        serverSelectionTimeoutMS=1000,
                                        socketTimeoutMS=1000)
        register_mock.assert_called_with('default', name='db_name',
                                         username='db_username',
                                         password='db_password', host='db_host',
                                         port='db_port')
        verify_mock.assert_called_once_with()

    @patch('mongoengine.connect')
    @patch('bg_utils._verify_db', Mock())
    def test_setup_database_connect_error(self, connect_mock):
        connect_mock.side_effect = ServerSelectionTimeoutError
        assert bg_utils.setup_database(MagicMock()) is False

    @patch('mongoengine.connect', Mock())
    @patch('mongoengine.register_connection', Mock())
    @patch('bg_utils.models.System')
    @patch('bg_utils.models.Request')
    def test_verify_db_same_indexes(self, request_mock, system_mock):
        request_mock.__name__ = 'Request'
        request_mock.list_indexes = Mock(return_value=['index1'])
        request_mock._get_collection = Mock(return_value=Mock(
            index_information=Mock(return_value=['index1'])))
        system_mock.__name__ = 'System'
        system_mock.list_indexes = Mock(return_value=['index1'])
        system_mock._get_collection = Mock(return_value=Mock(
            index_information=Mock(return_value=['index1'])))

        bg_utils._verify_db()
        assert system_mock.ensure_indexes.call_count == 1
        assert request_mock.ensure_indexes.call_count == 1

    @patch('mongoengine.connect', Mock())
    @patch('mongoengine.register_connection', Mock())
    @patch('bg_utils.models.System')
    @patch('bg_utils.models.Request')
    def test_verify_db_missing_index(self, request_mock, system_mock):
        request_mock.__name__ = 'Request'
        request_mock.list_indexes = Mock(return_value=['index1', 'index2'])
        request_mock._get_collection = Mock(return_value=Mock(
            index_information=Mock(return_value=['index1'])))
        system_mock.__name__ = 'System'
        system_mock.list_indexes = Mock(return_value=['index1', 'index2'])
        system_mock._get_collection = Mock(return_value=Mock(
            index_information=Mock(return_value=['index1'])))

        bg_utils._verify_db()
        assert system_mock.ensure_indexes.call_count == 1
        assert request_mock.ensure_indexes.call_count == 1

    @patch('mongoengine.connection.get_db')
    @patch('mongoengine.connect', Mock())
    @patch('mongoengine.register_connection', Mock())
    @patch('bg_utils.models.System')
    @patch('bg_utils.models.Request')
    def test_verify_db_successful_index_rebuild(self, request_mock, system_mock, get_db_mock):
        from pymongo.errors import OperationFailure
        request_mock.__name__ = 'Request'
        request_mock.list_indexes = Mock(side_effect=OperationFailure(""))
        request_mock._get_collection = Mock(return_value=Mock(
            index_information=Mock(return_value=['index1'])))
        system_mock.__name__ = 'System'
        system_mock.list_indexes = Mock(return_value=['index1'])
        system_mock._get_collection = Mock(return_value=Mock(
            index_information=Mock(return_value=['index1'])))

        db_mock = MagicMock()
        get_db_mock.return_value = db_mock

        bg_utils._verify_db()
        assert db_mock['request'].drop_indexes.call_count == 1
        assert request_mock.ensure_indexes.called is True

    @patch('mongoengine.connect', Mock())
    @patch('mongoengine.connection.get_db')
    @patch('bg_utils.models.System')
    @patch('bg_utils.models.Request')
    def test_verify_db_unsuccessful_index_drop(self, request_mock, system_mock, get_db_mock):
        from pymongo.errors import OperationFailure
        request_mock.__name__ = 'Request'
        request_mock.ensure_indexes = Mock(side_effect=OperationFailure(""))
        system_mock.__name__ = 'System'
        system_mock.ensure_indexes = Mock(side_effect=OperationFailure(""))
        get_db_mock.side_effect = OperationFailure("")

        with pytest.raises(OperationFailure):
            bg_utils._verify_db()

    @patch('mongoengine.connect', Mock())
    @patch('mongoengine.connection.get_db', MagicMock())
    @patch('bg_utils.models.System')
    @patch('bg_utils.models.Request')
    def test_verify_db_unsuccessful_index_rebuild(self, request_mock, system_mock):
        from pymongo.errors import OperationFailure
        request_mock.__name__ = 'Request'
        request_mock.ensure_indexes = Mock(side_effect=OperationFailure(""))
        system_mock.__name__ = 'System'
        system_mock.ensure_indexes = Mock(side_effect=OperationFailure(""))

        with pytest.raises(OperationFailure):
            bg_utils._verify_db()
