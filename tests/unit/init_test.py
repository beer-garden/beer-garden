import json
import unittest

from yapconf import YapconfSpec
from yapconf.exceptions import YapconfLoadError
from box import Box
from mock import Mock, patch, MagicMock

import bg_utils


class BgutilsTest(unittest.TestCase):

    def setUp(self):
        self.spec_base = {'log_config': {'required': False, 'default': None},
                          'log_file': {'required': False, 'default': None},
                          'log_level': {'required': False, 'default': 'INFO'},
                          'config': {'required': False, 'default': None}}
        self.spec = YapconfSpec(self.spec_base)

    def test_parse_args(self):
        cli_args = ["--log_config", "/path/to/log/config",
                    "--log_file", "/path/to/log/file",
                    "--log_level", "INFO",
                    "--config", "/path/to/config/file"]
        args = bg_utils.parse_args(self.spec, ['log_config', 'log_file', 'log_level', 'config'], cli_args)
        self.assertEqual(args.log_config, "/path/to/log/config")
        self.assertEqual(args.log_level, "INFO")
        self.assertEqual(args.log_file, "/path/to/log/file")
        self.assertEqual(args.config, "/path/to/config/file")

    def test_generate_config(self):
        config = bg_utils.generate_config(self.spec, ["--config", "/path/to/config"])
        self.assertIsNone(config.log_file)
        self.assertIsNone(config.log_config)
        self.assertEqual('INFO', config.log_level)
        self.assertEqual('/path/to/config', config.config)

    def test_generate_logging_config_not_to_file(self):
        config_generator = Mock(return_value={'foo': 'bar'})
        config_string = bg_utils.generate_logging_config(self.spec, config_generator, [])
        config_generator.assert_called_with('INFO', None)
        self.assertEqual(config_string, json.dumps({'foo': 'bar'}, indent=4, sort_keys=True))

    @patch('bg_utils.open')
    def test_generate_logging_config_to_file(self, open_mock):
        fake_file = Mock()
        fake_file.__exit__ = Mock()
        fake_file.__enter__ = Mock(return_value=fake_file)
        open_mock.return_value = fake_file
        config_generator = Mock(return_value={'foo': 'bar'})
        bg_utils.generate_logging_config(self.spec, config_generator, ["--log_config", "/path/to/log/config"])
        fake_file.write.assert_called_with(str(json.dumps({'foo': 'bar'}, indent=4, sort_keys=True)))

    def test_generate_config_no_file(self):
        self.spec.migrate_config_file = Mock()
        self.assertRaises(YapconfLoadError, bg_utils.generate_config_file, self.spec, [])
        #bg_utils.generate_config_file(self.spec, [])
        #self.spec.migrate_config_file.assert_called_with(
        #        {"log_file": None, "log_level": "INFO", "log_config": None, "config": None})

    def test_generate_config_with_file(self):
        self.spec.migrate_config_file = Mock()
        bg_utils.generate_config_file(self.spec, ["--config", "/path/to/config"])
        expected = Box({"log_file": None, "log_level": "INFO", "log_config": None, "config": "/path/to/config"})
        self.spec.migrate_config_file.assert_called_with('', expected,
            output_file_name="/path/to/config",
            output_file_type='json')

    def test_migrate_config_no_config_specified(self):
        with self.assertRaises(SystemExit):
            bg_utils.migrate_config(self.spec, [])

    def test_migrate_config_no_log_config_specified(self):
        self.spec.migrate_config_file = Mock()
        bg_utils.migrate_config(self.spec, ["--config", "/path/to/config"])
        self.assertIsNone(self.spec.get_item("log_config").default)
        self.spec.migrate_config_file.assert_called_with('/path/to/config', override_current=False,
                                                         current_config_file_type='json',
                                                         output_file_name='/path/to/config',
                                                         output_file_type='json',
                                                         create=True,
                                                         update_defaults=True)

    def test_migrate_config_with_log_config_specified(self):
        self.spec.migrate_config_file = Mock()
        bg_utils.migrate_config(self.spec, ["--config", "/path/to/config", "--log_config", "/path/to/log/config"])
        self.assertEqual(self.spec.get_item("log_config").default, "/path/to/log/config")
        self.spec.migrate_config_file.assert_called_with('/path/to/config', override_current=False,
                                                         current_config_file_type='json',
                                                         output_file_name='/path/to/config',
                                                         output_file_type='json',
                                                         create=True,
                                                         update_defaults=True)

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

    @patch('mongoengine.connect')
    @patch('bg_utils._verify_db', Mock())
    def test_setup_database_connect(self, connect_mock):
        app_config = Mock(db_name="db_name",
                          db_username="db_username",
                          db_password="db_password",
                          db_host="db_host",
                          db_port="db_port")
        bg_utils.setup_database(app_config)
        connect_mock.assert_called_with(db='db_name', username='db_username',
                                        password='db_password', host='db_host',
                                        port='db_port')

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
        self.assertEqual(system_mock.ensure_indexes.call_count, 1)
        self.assertEqual(request_mock.ensure_indexes.call_count, 1)

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
        self.assertEqual(system_mock.ensure_indexes.call_count, 1)
        self.assertEqual(request_mock.ensure_indexes.call_count, 1)

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
        self.assertEqual(db_mock['request'].drop_indexes.call_count, 1)
        self.assertTrue(request_mock.ensure_indexes.called)

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

        with self.assertRaises(OperationFailure):
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

        with self.assertRaises(OperationFailure):
            bg_utils.setup_database(Mock())
