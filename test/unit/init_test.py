import pytest
from yapconf import YapconfSpec
from box import Box
from mock import Mock, patch, MagicMock
from pymongo.errors import ServerSelectionTimeoutError
from yapconf import YapconfSpec

import bg_utils


@pytest.fixture
def spec():
    return YapconfSpec({'log_config': {'required': False, 'default': None},
                        'log_file': {'required': False, 'default': None},
                        'log_level': {'required': False, 'default': 'INFO'},
                        'config': {'required': False, 'default': None}})


class TestBgUtils(object):

    def test_parse_args(self, spec):
        cli_args = ["--log_config", "/path/to/log/config",
                    "--log_file", "/path/to/log/file",
                    "--log_level", "INFO",
                    "--config", "/path/to/config/file"]
        args = bg_utils.parse_args(spec, ['log_config', 'log_file', 'log_level', 'config'],
                                   cli_args)
        assert args.log_config == "/path/to/log/config"
        assert args.log_level == "INFO"
        assert args.log_file == "/path/to/log/file"
        assert args.config == "/path/to/config/file"

    def test_generate_config(self, spec):
        config = bg_utils._generate_config(spec, ["--config", "/path/to/config"])
        assert config.log_file is None
        assert config.log_config is None
        assert config.log_level == 'INFO'
        assert config.config == '/path/to/config'

    def test_generate_config_file(self, spec):
        spec._write_dict_to_file = Mock()
        bg_utils.generate_config_file(spec, ["--config", "/path/to/config"])
        expected = Box({"log_file": None, "log_level": "INFO", "log_config": None,
                        "config": "/path/to/config"})
        spec._write_dict_to_file.assert_called_with(expected, '/path/to/config', 'json')

    def test_generate_config_file_no_config(self, spec):
        spec._write_dict_to_file = Mock()
        bg_utils.generate_config_file(spec, [])
        assert spec._write_dict_to_file.called is False

    def test_update_config(self, spec):
        spec.update_defaults = Mock()
        spec.migrate_config_file = Mock()
        bg_utils.update_config_file(spec, ["--config", "/path/to/config"])

        expected = Box({"log_file": None, "log_level": "INFO", "log_config": None,
                        "config": "/path/to/config"})
        spec.migrate_config_file.assert_called_once_with(expected.config, update_defaults=True)

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

    @patch('bg_utils.logging.config.dictConfig')
    def test_setup_application_logging_no_log_config(self, config_mock):
        app_config = Mock(log_config=None)
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
            spec, config_generator, ['--log_config', str(config_path)])

        assert logging_config == generated_config

    @patch('mongoengine.connect')
    @patch('bg_utils._verify_db', Mock())
    def test_setup_database_connect(self, connect_mock):
        app_config = Mock(db_name="db_name", db_username="db_username", db_password="db_password",
                          db_host="db_host", db_port="db_port")
        self.assertTrue(bg_utils.setup_database(app_config))
        connect_mock.assert_called_with(db='db_name', username='db_username',
                                        password='db_password', host='db_host', port='db_port',
                                        serverSelectionTimeoutMS=1000, socketTimeoutMS=1000)

    @patch('mongoengine.connect')
    @patch('bg_utils._verify_db', Mock())
    def test_setup_database_connect_error(self, connect_mock):
        app_config = Mock(db_name="db_name", db_username="db_username", db_password="db_password",
                          db_host="db_host", db_port="db_port")
        connect_mock.side_effect = ServerSelectionTimeoutError
        self.assertFalse(bg_utils.setup_database(app_config))

    @patch('mongoengine.connect', Mock())
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

        bg_utils.setup_database(Mock())
        assert system_mock.ensure_indexes.call_count == 1
        assert request_mock.ensure_indexes.call_count == 1

    @patch('mongoengine.connect', Mock())
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

        bg_utils.setup_database(Mock())
        assert system_mock.ensure_indexes.call_count == 1
        assert request_mock.ensure_indexes.call_count == 1

    @patch('mongoengine.connection.get_db')
    @patch('mongoengine.connect', Mock())
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

        bg_utils.setup_database(Mock())
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
            bg_utils.setup_database(Mock())

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
            bg_utils.setup_database(Mock())
