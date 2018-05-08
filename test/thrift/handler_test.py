import unittest

import mongoengine
from mock import MagicMock, Mock, PropertyMock, patch, call
from pyrabbit2.http import HTTPError

import bg_utils
from bartender.thrift.handler import BartenderHandler
from brewtils.errors import ModelValidationError


class BartenderHandlerTest(unittest.TestCase):

    def setUp(self):
        self.registry = Mock()
        self.clients = MagicMock()
        self.plugin_manager = Mock()
        self.request_validator = Mock()

        self.handler = BartenderHandler(self.registry, self.clients, self.plugin_manager,
                                        self.request_validator)
        self.handler.parser = Mock()

    @patch('bg_utils.models.Request.find_or_none', Mock(side_effect=mongoengine.ValidationError))
    def test_process_request_bad_request(self):
        self.assertRaises(bg_utils.bg_thrift.InvalidRequest, self.handler.processRequest, 'id')

    @patch('bg_utils.models.Request.find_or_none', Mock(return_value=None))
    def test_process_request_none(self):
        self.assertRaises(bg_utils.bg_thrift.InvalidRequest, self.handler.processRequest, 'id')

    @patch('bg_utils.models.Request.find_or_none', Mock())
    def test_process_request_bad_backend(self):
        self.request_validator.validate_request = Mock(side_effect=ModelValidationError)
        self.assertRaises(bg_utils.bg_thrift.InvalidRequest, self.handler.processRequest, 'id')

    @patch('bg_utils.models.Request.find_or_none')
    def test_process_request(self, find_mock):
        request = Mock()
        find_mock.return_value = request
        self.request_validator.validate_request.return_value = request

        self.handler.processRequest('id')
        find_mock.assert_called_once_with('id')
        self.clients['pika'].publish_request.assert_called_once_with(request, confirm=True,
                                                                     mandatory=True)

    @patch('bg_utils.models.Request.find_or_none')
    def test_process_request_fail(self, find_mock):
        request = Mock()
        find_mock.return_value = request
        self.request_validator.validate_request.return_value = request
        self.clients['pika'].publish_request.return_value = False

        self.assertRaises(bg_utils.bg_thrift.PublishException, self.handler.processRequest, 'id')

    @patch('bartender.thrift.handler.get_routing_key', Mock(return_value='a'))
    @patch('bartender.thrift.handler.get_routing_keys', Mock(return_value=['b']))
    @patch('bartender.thrift.handler.BartenderHandler._get_system', Mock())
    @patch('bartender.thrift.handler.BartenderHandler._get_instance')
    def test_initialize_instance(self, get_instance_mock):
        instance_mock = Mock(metadata={})
        get_instance_mock.return_value = instance_mock

        self.handler.initializeInstance('id')
        self.assertEqual('rabbitmq', instance_mock.queue_type)
        self.assertEqual('INITIALIZING', instance_mock.status)
        self.assertEqual(2, self.clients['pika'].setup_queue.call_count)
        self.assertTrue(self.clients['pika'].start.called)

    @patch('bartender.thrift.handler.BartenderHandler._get_instance', Mock())
    @patch('bartender.thrift.handler.BartenderHandler._get_plugin_from_instance_id')
    def test_start_instance(self, plugin_mock):
        plugin_mock.return_value = 'the_plugin'
        self.handler.startInstance('instance_id')
        self.plugin_manager.start_plugin.assert_called_once_with('the_plugin')

    @patch('bartender.thrift.handler.BartenderHandler._get_instance', Mock())
    @patch('bartender.thrift.handler.BartenderHandler._get_plugin_from_instance_id')
    def test_start_instance_not_found(self, plugin_mock):
        plugin_mock.side_effect = bg_utils.bg_thrift.InvalidSystem('', 'ERROR MESSAGE')
        self.assertRaises(bg_utils.bg_thrift.InvalidSystem, self.handler.startInstance,
                          'instance_id')
        plugin_mock.assert_called_once_with('instance_id')

    @patch('bartender.thrift.handler.BartenderHandler._get_instance', Mock())
    @patch('bartender.thrift.handler.BartenderHandler._get_plugin_from_instance_id')
    def test_stop_instance_local(self, plugin_mock):
        plugin_mock.return_value = 'the_plugin'
        self.handler.stopInstance('instance_id')
        self.plugin_manager.stop_plugin.assert_called_once_with('the_plugin')

    @patch('bartender.thrift.handler.BartenderHandler._get_instance', Mock())
    @patch('bartender.thrift.handler.BartenderHandler._get_system', Mock())
    @patch('bartender.thrift.handler.BartenderHandler._get_plugin_from_instance_id')
    def test_stop_instance_remote(self, plugin_mock):
        plugin_mock.return_value = None

        self.handler.stopInstance('instance_id')
        plugin_mock.assert_called_once_with('instance_id')
        self.assertTrue(self.clients['pika'].stop.called)

    @patch('bartender.thrift.handler.BartenderHandler._get_instance', Mock())
    @patch('bartender.thrift.handler.BartenderHandler._get_plugin_from_instance_id')
    def test_stop_instance_error(self, plugin_mock):
        plugin_mock.side_effect = bg_utils.bg_thrift.InvalidSystem('', 'ERROR MESSAGE')
        self.assertRaises(bg_utils.bg_thrift.InvalidSystem, self.handler.stopInstance,
                          'instance_id')
        plugin_mock.assert_called_once_with('instance_id')

    @patch('bartender.thrift.handler.BartenderHandler.stopInstance')
    @patch('bartender.thrift.handler.BartenderHandler.startInstance')
    def test_restart_system_calls(self, start_mock, stop_mock):
        self.handler.restartInstance('instance_id')
        start_mock.assert_called_once_with('instance_id')
        stop_mock.assert_called_once_with('instance_id')

    @patch('bartender.thrift.handler.System')
    def test_reload_system_not_found(self, system_mock):
        system_mock.objects.get = Mock(side_effect=mongoengine.DoesNotExist)
        self.assertRaises(bg_utils.bg_thrift.InvalidSystem, self.handler.reloadSystem, 'id')

    @patch('bartender.thrift.handler.System')
    def test_reload_system_calls(self, system_mock):
        fake_system = Mock(version='0.0.1')
        type(fake_system).name = PropertyMock(return_value='name')
        system_mock.objects.get = Mock(return_value=fake_system)

        self.handler.reloadSystem('id')
        self.plugin_manager.reload_system.assert_called_once_with('name', '0.0.1')

    @patch('bartender.thrift.handler.System')
    def test_reload_exception(self, system_mock):
        fake_system = Mock(version='0.0.1')
        type(fake_system).name = PropertyMock(return_value='name')
        system_mock.objects.get = Mock(return_value=fake_system)
        self.plugin_manager.reload_system = Mock(side_effect=Exception)
        self.assertRaises(Exception, self.handler.reloadSystem, 'id')

    @patch('bartender.thrift.handler.System')
    def test_reload_exception_does_not_exist_error(self, system_mock):
        system_mock.objects.get = Mock(side_effect=mongoengine.DoesNotExist)
        self.assertRaises(bg_utils.bg_thrift.InvalidSystem, self.handler.reloadSystem, 'id')

    @patch('bartender.thrift.handler.System')
    def test_remove_local_system(self, system_mock):
        fake_system = MagicMock(version='0.0.1')
        type(fake_system).name = PropertyMock(return_value='name')
        fake_system.instances = [Mock(name='default', status='STOPPED',
                                      queue_info={'admin': {'name': 'admin'},
                                                  'request': {'name': 'request'}})]
        system_mock.objects.get = Mock(return_value=fake_system)

        fake_plugin = Mock(unique_name='name[default]-0.0.1')
        self.registry.get_plugins_by_system.return_value = [fake_plugin]

        self.handler.removeSystem('id')
        self.clients['pyrabbit'].destroy_queue.assert_has_calls([call('request',
                                                                      force_disconnect=False),
                                                                 call('admin',
                                                                      force_disconnect=False)])
        self.assertTrue(fake_system.deep_delete.called)

    @patch('bartender.thrift.handler.sleep', Mock())
    @patch('bartender.config')
    @patch('bartender.thrift.handler.System')
    def test_remove_remote_system(self, system_mock, config_mock):
        config_mock.plugin.local.timeout.shutdown = 1
        fake_system = MagicMock(version='0.0.1')
        type(fake_system).name = PropertyMock(return_value='name')
        fake_system.instances = [Mock(name='default', status='RUNNING',
                                      queue_info={'admin': {'name': 'admin'},
                                                  'request': {'name': 'request'}})]
        system_mock.objects.get = Mock(return_value=fake_system)

        self.registry.get_plugins_by_system.return_value = []

        self.handler.removeSystem('id')
        self.assertTrue(self.clients['pika'].stop.called)
        self.clients['pyrabbit'].destroy_queue.assert_has_calls([call('request',
                                                                      force_disconnect=True),
                                                                 call('admin',
                                                                      force_disconnect=True)])
        self.assertTrue(fake_system.deep_delete.called)

    @patch('bartender.thrift.handler.System')
    def test_remove_system_errors(self, system_mock):
        fake_system = MagicMock(version='0.0.1')
        type(fake_system).name = PropertyMock(return_value='name')
        fake_system.instances = [Mock(name='default', queue_info={'admin': {'name': 'admin_queue'},
                                                                  'request':
                                                                      {'name': 'request_queue'}})]
        system_mock.objects.get = Mock(return_value=fake_system)

        fake_plugin = Mock(unique_name='name[default]-0.0.1')
        self.registry.get_plugins_by_system.return_value = [fake_plugin]

        self.clients['pyrabbit'].disconnect_consumers.side_effect = Exception
        self.clients['pyrabbit'].clear_queue.side_effect = Exception
        self.clients['pyrabbit'].delete_queue.side_effect = Exception

        self.handler.removeSystem('id')
        self.assertTrue(fake_system.deep_delete.called)

    @patch('bartender.thrift.handler.System')
    def test_remove_system_errors_2(self, system_mock):
        fake_system = MagicMock(version='0.0.1')
        type(fake_system).name = PropertyMock(return_value='name')
        fake_system.instances = [Mock(name='default', queue_info={'admin': {'name': 'admin_queue'},
                                                                  'request':
                                                                      {'name': 'request_queue'}})]
        system_mock.objects.get = Mock(return_value=fake_system)

        fake_plugin = Mock(unique_name='name[default]-0.0.1')
        self.registry.get_plugins_by_system.return_value = [fake_plugin]

        self.clients['pyrabbit'].disconnect_consumers.side_effect = Exception
        self.clients['pyrabbit'].clear_queue.side_effect = Exception
        self.clients['pyrabbit'].delete_queue.side_effect = HTTPError({}, 400, "Reason")

        self.handler.removeSystem('id')
        self.assertTrue(fake_system.deep_delete.called)

    @patch('bartender.thrift.handler.System')
    def test_remove_system_not_found_exception(self, system_mock):
        system_mock.objects.get = Mock(side_effect=mongoengine.DoesNotExist)
        self.assertRaises(bg_utils.bg_thrift.InvalidSystem, self.handler.removeSystem, 'id')

    @patch('bartender.thrift.handler.System')
    def test_remove_system_random_exception(self, system_mock):
        system_mock.objects.get = Mock(side_effect=ValueError)
        self.assertRaises(ValueError, self.handler.removeSystem, 'id')

    def test_rescan_system_directory_calls(self):
        self.handler.rescanSystemDirectory()
        self.assertEqual(self.plugin_manager.scan_plugin_path.call_count, 1)

    def test_rescan_system_directory_exception(self):
        self.plugin_manager.scan_plugin_path = Mock(side_effect=Exception)
        self.assertRaises(Exception, self.handler.rescanSystemDirectory)
        self.assertEqual(self.plugin_manager.scan_plugin_path.call_count, 1)

    def test_get_queue_info(self):
        self.clients['pyrabbit'].get_queue_size = Mock(return_value=1)
        queue_info = self.handler.getQueueInfo('system', 'version', 'instance')
        self.assertEqual(queue_info.name, 'system.version.instance')
        self.assertEqual(queue_info.size, 1)

    def test_get_queue_info_exception(self):
        self.clients['pyrabbit'].get_queue_size = Mock(side_effect=ValueError)
        self.assertRaises(ValueError, self.handler.getQueueInfo, 'sys', 'ver', 'ins')

    def test_clear_queue(self):
        self.handler.clearQueue('queue_name')
        self.clients['pyrabbit'].clear_queue.assert_called_once_with('queue_name')

    def test_clear_queue_404_http_exception(self):
        self.clients['pyrabbit'].clear_queue = Mock(side_effect=HTTPError({}, 404, "Reason"))
        self.assertRaises(bg_utils.bg_thrift.InvalidSystem, self.handler.clearQueue, 'queue_name')
        self.clients['pyrabbit'].clear_queue.assert_called_once_with('queue_name')

    def test_clear_queue_other_http_exception(self):
        self.clients['pyrabbit'].clear_queue = Mock(side_effect=HTTPError({}, 500, "Reason"))
        self.assertRaises(HTTPError, self.handler.clearQueue, 'queue_name')

    def test_clear_queue_other_exception(self):
        self.clients['pyrabbit'].clear_queue = Mock(side_effect=ValueError('Reason'))
        self.assertRaises(ValueError, self.handler.clearQueue, 'queue_name')

    @patch('bartender.thrift.handler.System')
    def test_clean_all_queues(self, system_mock):
        fake_instance = Mock(status='RUNNING')
        type(fake_instance).name = PropertyMock(return_value='inst')

        fake_system = Mock(version='0.0.1', instances=[fake_instance])
        type(fake_system).name = PropertyMock(return_value='name')
        system_mock.objects.all = MagicMock(return_value=[fake_system, fake_system])

        self.handler.clearAllQueues()
        self.assertEqual(2, self.clients['pyrabbit'].clear_queue.call_count)

    @patch('bartender.thrift.handler.System')
    def test_clean_all_queues_exception(self, system_mock):
        system_mock.objects.all.side_effect = ValueError('Reason')

        self.assertRaises(ValueError, self.handler.clearAllQueues)

    @patch('bartender._version', MagicMock(__version__='version'))
    def test_get_version(self):
        self.assertEqual('version', self.handler.getVersion())

    def test_ping(self):
        self.handler.logger = Mock()
        self.handler.ping()
        self.handler.logger.info.assert_called_with('Ping.')

    @patch('bartender.thrift.handler.BartenderHandler._get_instance')
    @patch('bartender.thrift.handler.BartenderHandler._get_system')
    def test_get_plugin_from_instance_id(self, get_system_mock, get_instance_mock):
        id_mock = Mock()

        self.assertEqual(self.registry.get_plugin.return_value,
                         self.handler._get_plugin_from_instance_id(id_mock))
        get_instance_mock.assert_called_once_with(id_mock)
        get_system_mock.assert_called_once_with(get_instance_mock.return_value)
        self.registry.get_plugin.assert_called_once_with(self.registry.get_unique_name.return_value)

    @patch('bartender.thrift.handler.Instance.objects')
    def test_get_instance(self, objects_mock):
        self.assertEqual(objects_mock.get.return_value, self.handler._get_instance(Mock()))

    @patch('bartender.thrift.handler.Instance.objects')
    def test_get_instance_not_found(self, objects_mock):
        objects_mock.get.side_effect = mongoengine.DoesNotExist
        self.assertRaises(bg_utils.bg_thrift.InvalidSystem, self.handler._get_instance, Mock())

    @patch('bartender.thrift.handler.System.objects')
    def test_get_system(self, objects_mock):
        self.assertEqual(objects_mock.get.return_value, self.handler._get_system(Mock()))

    @patch('bartender.thrift.handler.System.objects')
    def test_get_system_not_found(self, objects_mock):
        objects_mock.get.side_effect = mongoengine.DoesNotExist
        self.assertRaises(bg_utils.bg_thrift.InvalidSystem, self.handler._get_system, Mock())
