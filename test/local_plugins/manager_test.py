import unittest

from box import Box
from mock import call, patch, MagicMock, Mock, PropertyMock

import bartender
from bartender.errors import PluginStartupError
from bartender.local_plugins.manager import LocalPluginsManager


class LocalPluginsManagerTest(unittest.TestCase):

    def setUp(self):
        bartender.config = Box(default_box=True)

        self.fake_plugin_loader = Mock()
        self.fake_plugin_validator = Mock()
        self.clients = MagicMock()

        self.instance_mock = Mock(status='RUNNING')
        type(self.instance_mock).name = PropertyMock(return_value='default')
        self.system_mock = Mock(version='1.0.0', instances=[self.instance_mock])
        type(self.system_mock).name = PropertyMock(return_value='system_name')

        self.fake_plugin = Mock(system=self.system_mock, unique_name='unique_name',
                                path_to_plugin='path/name-0.0.1',
                                requirements=[], entry_point='main.py', plugin_args=[],
                                instance_name='default',
                                status='RUNNING')

        self.registry = Mock(get_plugin=Mock(return_value=self.fake_plugin),
                             get_unique_plugin_names=Mock(return_value=['system_name']),
                             get_all_plugins=Mock(return_value=[self.fake_plugin]),
                             get_plugins_by_system=Mock(return_value=[self.fake_plugin]))

        self.manager = LocalPluginsManager(self.fake_plugin_loader, self.fake_plugin_validator,
                                           self.registry, self.clients)

    def test_start_plugin_initializing(self):
        self.fake_plugin.status = 'INITIALIZING'
        self.assertTrue(self.manager.start_plugin(self.fake_plugin))
        self.fake_plugin.start.assert_called_once_with()

    def test_start_plugin_running(self):
        self.assertTrue(self.manager.start_plugin(self.fake_plugin))
        self.assertFalse(self.fake_plugin.start.called)

    def test_start_plugin_bad_state(self):
        self.fake_plugin.status = 'BAD STATUS'
        self.assertRaises(PluginStartupError, self.manager.start_plugin, self.fake_plugin)
        self.assertFalse(self.fake_plugin.start.called)

    @patch('bartender.local_plugins.manager.LocalPluginRunner')
    def test_start_plugin_stopped(self, plugin_mock):
        self.fake_plugin.status = 'STOPPED'
        new_plugin = Mock()
        plugin_mock.return_value = new_plugin

        self.assertTrue(self.manager.start_plugin(self.fake_plugin))
        self.assertEqual(0, self.fake_plugin.start.call_count)
        self.registry.remove.assert_called_once_with(self.fake_plugin.unique_name)
        self.registry.register_plugin.assert_called_once_with(new_plugin)
        self.assertTrue(plugin_mock.called)
        new_plugin.start.assert_called_once_with()

    def test_stop_plugin(self):
        self.fake_plugin.is_alive = Mock(return_value=False)

        self.manager.stop_plugin(self.fake_plugin)
        self.fake_plugin.stop.assert_called_once_with()
        self.assertTrue(self.clients['pika'].stop.called)
        self.assertTrue(self.fake_plugin.join.called)
        self.assertFalse(self.fake_plugin.kill.called)

    def test_stop_plugin_already_stopped(self):
        self.fake_plugin.status = 'STOPPED'
        self.manager.stop_plugin(self.fake_plugin)
        self.assertEqual(self.fake_plugin.stop.call_count, 0)

    def test_stop_plugin_unknown_status(self):
        self.fake_plugin.status = 'UNKNOWN'
        self.manager.stop_plugin(self.fake_plugin)
        self.fake_plugin.stop.assert_called_once_with()

    def test_stop_plugin_exception(self):
        self.fake_plugin.stop = Mock(side_effect=Exception)
        self.fake_plugin.is_alive = Mock(return_value=True)

        self.manager.stop_plugin(self.fake_plugin)
        self.assertTrue(self.fake_plugin.kill.called)
        self.assertFalse(self.fake_plugin.join.called)
        self.assertEqual('DEAD', self.fake_plugin.status)

    def test_unsuccessful_stop_plugin(self):
        self.fake_plugin.is_alive = Mock(return_value=True)

        self.manager.stop_plugin(self.fake_plugin)
        self.assertTrue(self.fake_plugin.kill.called)
        self.assertTrue(self.fake_plugin.join.called)
        self.assertEqual('DEAD', self.fake_plugin.status)

    @patch('bartender.local_plugins.manager.LocalPluginsManager.start_plugin')
    @patch('bartender.local_plugins.manager.LocalPluginsManager.stop_plugin')
    def test_restart(self, stop_mock, start_mock):
        self.manager.restart_plugin(self.fake_plugin)
        stop_mock.assert_called_once_with(self.fake_plugin)
        start_mock.assert_called_once_with(self.fake_plugin)

    def test_reload_system(self):
        self.fake_plugin.status = 'STOPPED'
        self.fake_plugin_validator.validate_plugin = Mock(return_value=True)

        self.manager.reload_system(self.fake_plugin.system.name, self.fake_plugin.system.version)
        self.registry.remove.assert_called_with(self.fake_plugin.unique_name)
        self.fake_plugin_loader.load_plugin.assert_called_with(self.fake_plugin.path_to_plugin)

    def test_reload_system_none(self):
        self.registry.get_plugins_by_system = Mock(return_value=[])
        self.assertRaises(Exception, self.manager.reload_system, 'name', 'version')

    def test_reload_system_fail_validation(self):
        self.fake_plugin_validator.validate_plugin = Mock(return_value=False)
        self.assertRaises(Exception, self.manager.reload_system, 'name', 'version')

    def test_reload_system_running(self):
        self.fake_plugin.status = 'RUNNING'
        self.fake_plugin_validator.validate_plugin = Mock(return_value=True)
        self.assertRaises(Exception, self.manager.reload_system, 'name', 'version')

    @patch('bartender.local_plugins.manager.LocalPluginsManager._start_multiple_plugins')
    def test_start_all_plugins(self, start_multiple_mock):
        self.manager.start_all_plugins()
        start_multiple_mock.assert_called_once_with([self.fake_plugin])

    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_all_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_running_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_failed_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager.start_plugin')
    def test_start_multiple_plugins_empty(self, start_mock):
        self.manager._start_multiple_plugins([])
        self.assertEqual(start_mock.call_count, 0)

    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_all_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_running_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_failed_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager.start_plugin')
    def test_start_multiple_plugins_no_requirements(self, start_mock):
        fake_plugin_2 = Mock(system=self.system_mock, unique_name='unique_name2',
                             path_to_plugin='path/name-0.0.1',
                             requirements=[], entry_point='main.py', plugin_args=[],
                             instance_name='default2',
                             status='RUNNING')

        self.manager._start_multiple_plugins([self.fake_plugin, fake_plugin_2])
        start_mock.assert_has_calls([call(self.fake_plugin), call(fake_plugin_2)], any_order=True)

    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_all_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_running_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_failed_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._mark_as_failed')
    def test_start_multiple_plugins_invalid_requirements(self, fail_mock):
        self.fake_plugin.requirements = ['DNE']
        self.manager._start_multiple_plugins([self.fake_plugin])
        fail_mock.assert_called_once_with(self.fake_plugin)

    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_all_system_names',
           Mock(return_value=['system_name', 'system_name_2']))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_running_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_failed_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager.start_plugin')
    def test_start_multiple_plugins(self, start_mock):
        system_mock_2 = Mock(version='1.0.0', instances=[Mock(name='default')])
        type(system_mock_2).name = PropertyMock(return_value='system_name_2')
        fake_plugin_2 = Mock(system=system_mock_2, unique_name='unique_name2',
                             path_to_plugin='path/name-0.0.1',
                             requirements=['system_name'], entry_point='main.py', plugin_args=[],
                             instance_name='default2', status='RUNNING')

        self.manager._start_multiple_plugins([fake_plugin_2, self.fake_plugin])
        start_mock.assert_has_calls([call(self.fake_plugin), call(fake_plugin_2)], any_order=True)

    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_all_system_names',
           Mock(return_value=['system_name', 'system_name_2']))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_running_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_failed_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager.start_plugin')
    def test_start_multiple_plugins_skip_first(self, start_mock):

        system_mock_2 = Mock(version='1.0.0', instances=[Mock(name='default')])
        type(system_mock_2).name = PropertyMock(return_value='system_name_2')
        fake_plugin_2 = Mock(system=system_mock_2, unique_name='unique_name2',
                             path_to_plugin='path/name-0.0.1',
                             requirements=['system_name'], entry_point='main.py', plugin_args=[],
                             instance_name='default2', status='RUNNING')

        self.manager._start_multiple_plugins([self.fake_plugin, fake_plugin_2])
        start_mock.assert_has_calls([call(self.fake_plugin), call(fake_plugin_2)], any_order=True)

    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_all_system_names',
           Mock(return_value=['system_name', 'system_name_2']))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_running_system_names',
           Mock(return_value=['system_name']))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_failed_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager.start_plugin')
    def test_start_multiple_plugins_requirement_already_running(self, start_mock):

        system_mock_2 = Mock(version='1.0.0', instances=[Mock(name='default')])
        type(system_mock_2).name = PropertyMock(return_value='system_name_2')
        fake_plugin_2 = Mock(system=system_mock_2, unique_name='unique_name2',
                             path_to_plugin='path/name-0.0.1',
                             requirements=['system_name'], entry_point='main.py', plugin_args=[],
                             instance_name='default2', status='RUNNING')

        self.manager._start_multiple_plugins([fake_plugin_2])
        start_mock.assert_has_calls([call(fake_plugin_2)], any_order=True)

    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_all_system_names',
           Mock(return_value=['system_name', 'system_name_2']))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_running_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._get_failed_system_names',
           Mock(return_value=[]))
    @patch('bartender.local_plugins.manager.LocalPluginsManager._mark_as_failed')
    @patch('bartender.local_plugins.manager.LocalPluginsManager.start_plugin')
    def test_start_multiple_plugins_failed_requirement_start(self, start_mock, fail_mock):

        system_mock_2 = Mock(version='1.0.0', instances=[Mock(name='default')])
        type(system_mock_2).name = PropertyMock(return_value='system_name_2')
        fake_plugin_2 = Mock(system=system_mock_2, unique_name='unique_name2',
                             path_to_plugin='path/name-0.0.1',
                             requirements=['system_name'], entry_point='main.py', plugin_args=[],
                             instance_name='default2', status='RUNNING')

        start_mock.return_value = False

        self.manager._start_multiple_plugins([self.fake_plugin, fake_plugin_2])
        start_mock.assert_called_once_with(self.fake_plugin)
        fail_mock.assert_called_once_with(fake_plugin_2)

    @patch('bartender.local_plugins.manager.System')
    def test_get_all_system_names(self, system_mock):
        system_mock.objects.return_value = [self.system_mock]
        self.assertEqual([self.system_mock.name], self.manager._get_all_system_names())

    @patch('bartender.local_plugins.manager.LocalPluginsManager.stop_plugin')
    def test_stop_all_plugins(self, stop_mock):
        self.manager.stop_all_plugins()
        stop_mock.assert_called_once_with(self.fake_plugin)

    @patch('bartender.local_plugins.manager.LocalPluginsManager.stop_plugin')
    def test_stop_all_plugins_empty(self, stop_mock):
        self.registry.get_all_plugins = Mock(return_value=[])
        self.manager.stop_all_plugins()
        self.assertEqual(stop_mock.call_count, 0)

    @patch('bartender.local_plugins.manager.LocalPluginsManager.stop_plugin')
    def test_stop_all_plugins_exception(self, stop_mock):
        stop_mock.side_effect = [Exception(), None]
        self.manager.logger = Mock()
        self.registry.get_all_plugins = Mock(return_value=[self.fake_plugin, self.fake_plugin])

        self.manager.stop_all_plugins()
        self.assertTrue(self.manager.logger.exception.called)
        self.assertTrue(self.manager.logger.error.called)
        stop_mock.assert_has_calls([call(self.fake_plugin), call(self.fake_plugin)])

    @patch('bartender.local_plugins.manager.LocalPluginsManager._start_multiple_plugins', Mock())
    def test_scan_plugin_path_no_change(self):
        self.fake_plugin_loader.scan_plugin_path = Mock(
            return_value=[self.fake_plugin.path_to_plugin])
        self.registry.get_all_plugins = Mock(return_value=[self.fake_plugin])
        self.manager.scan_plugin_path()
        self.assertEqual(0, self.fake_plugin_loader.load_plugin.call_count)

    @patch('bartender.local_plugins.manager.LocalPluginsManager._start_multiple_plugins')
    def test_scan_plugin_path_one_new(self, start_mock):
        self.fake_plugin_loader.scan_plugin_path = Mock(
            return_value=[self.fake_plugin.path_to_plugin])
        self.fake_plugin_loader.load_plugin = Mock(return_value=[self.fake_plugin])
        self.registry.get_all_plugins = Mock(return_value=[])

        self.manager.scan_plugin_path()
        self.fake_plugin_loader.load_plugin.assert_called_once_with(self.fake_plugin.path_to_plugin)
        start_mock.assert_called_once_with([self.fake_plugin])

    @patch('bartender.local_plugins.manager.LocalPluginsManager._start_multiple_plugins')
    def test_scan_plugin_path_two_new_could_not_load_one(self, start_mock):
        self.fake_plugin_loader.scan_plugin_path = Mock(
            return_value=[self.fake_plugin.path_to_plugin, 'path/tw-0.0.1'])
        self.fake_plugin_loader.load_plugin = Mock(side_effect=[[self.fake_plugin], []])
        self.registry.get_all_plugins = Mock(return_value=[])

        self.manager.scan_plugin_path()
        self.fake_plugin_loader.load_plugin.assert_has_calls([call(self.fake_plugin.path_to_plugin),
                                                              call('path/tw-0.0.1')],
                                                             any_order=True)
        start_mock.assert_called_once_with([self.fake_plugin])

    @patch('bartender.local_plugins.manager.LocalPluginsManager._start_multiple_plugins')
    def test_scan_plugin_path_one_exception(self, start_mock):
        self.fake_plugin_loader.scan_plugin_path = Mock(
            return_value=[self.fake_plugin.path_to_plugin, 'path/tw-0.0.1'])
        self.fake_plugin_loader.load_plugin = Mock(side_effect=[[self.fake_plugin], Exception])
        self.registry.get_all_plugins = Mock(return_value=[])

        self.manager.scan_plugin_path()
        self.fake_plugin_loader.load_plugin.assert_has_calls([call(self.fake_plugin.path_to_plugin),
                                                              call('path/tw-0.0.1')],
                                                             any_order=True)
        start_mock.assert_called_once_with([self.fake_plugin])

    def test_pause_plugin_none(self):
        self.registry.get_plugin = Mock(return_value=None)
        self.manager.logger = Mock()
        self.manager.pause_plugin('unique_name')
        self.assertEqual(self.manager.logger.warning.call_count, 1)

    def test_pause_plugin_not_running(self):
        self.fake_plugin.status = 'STOPPED'
        self.manager.pause_plugin('unique_name')
        self.assertEqual(self.fake_plugin.status, 'STOPPED')

    def test_pause_plugin_running(self):
        self.fake_plugin.status = 'RUNNING'
        self.manager.pause_plugin('unique_name')
        self.assertEqual(self.fake_plugin.status, 'PAUSED')

    def test_unpause_plugin_none(self):
        self.registry.get_plugin = Mock(return_value=None)
        self.manager.logger = Mock()
        self.manager.unpause_plugin('unique_name')
        self.assertTrue(self.manager.logger.warning.called)

    def test_unpause_plugin_not_paused(self):
        self.fake_plugin.status = 'RUNNING'
        self.manager.unpause_plugin('unique_name')
        self.assertEqual(self.fake_plugin.status, 'RUNNING')

    def test_unpause_plugin_paused(self):
        self.fake_plugin.status = 'PAUSED'
        self.manager.unpause_plugin('unique_name')
        self.assertEqual(self.fake_plugin.status, 'RUNNING')

    @patch('bartender.local_plugins.manager.System.find_unique')
    def test_mark_as_failed(self, find_system_mock):
        find_system_mock.return_value = self.system_mock

        self.manager._mark_as_failed(self.fake_plugin)
        self.assertEqual(self.instance_mock.status, 'DEAD')
        self.assertTrue(self.system_mock.deep_save.called)

    @patch('bartender.local_plugins.manager.System.objects')
    def test_get_failed_system_names(self, objects_mock):

        # Construct another fake system with all dead instances
        instance_mock_2 = Mock(status='DEAD')
        type(instance_mock_2).name = PropertyMock(return_value='default')
        system_mock_2 = Mock(version='1.0.0', instances=[instance_mock_2])
        type(system_mock_2).name = PropertyMock(return_value='dead_system')

        objects_mock.return_value = [self.system_mock, system_mock_2]

        failed_plugins = self.manager._get_failed_system_names()
        self.assertEqual(failed_plugins, ['dead_system'])

    @patch('bartender.local_plugins.manager.System.objects')
    def test_get_failed_system_names_one_live_instance(self, objects_mock):
        instance_mock_2 = Mock(status='DEAD')
        type(instance_mock_2).name = PropertyMock(return_value='default_2')
        self.system_mock.instances = [self.instance_mock, instance_mock_2]

        objects_mock.return_value = [self.system_mock]

        failed_plugins = self.manager._get_failed_system_names()
        self.assertFalse(failed_plugins)
