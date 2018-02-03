import unittest

from mock import Mock, PropertyMock

from bartender.local_plugins.registry import LocalPluginRegistry


class RegistryTest(unittest.TestCase):

    def setUp(self):
        self.registry = LocalPluginRegistry()

        self.fake_system_1 = Mock(version='0.0.1')
        self.fake_system_2 = Mock(version='0.0.1')
        type(self.fake_system_1).name = PropertyMock(return_value='plugin1')
        type(self.fake_system_2).name = PropertyMock(return_value='plugin2')

        self.mock_plugin_1 = Mock(system=self.fake_system_1, unique_name='plugin1[inst1]-0.0.1', instance_name='inst1',
                                  status='INITIALIZING')
        self.mock_plugin_2 = Mock(system=self.fake_system_2, unique_name='plugin2[inst1]-0.0.1', instance_name='inst1',
                                  status='INITIALIZING')
        self.mock_plugin_3 = Mock(system=self.fake_system_2, unique_name='plugin2[inst2]-0.0.1', instance_name='inst2',
                                  status='INITIALIZING')

        self.registry._registry = [self.mock_plugin_1, self.mock_plugin_2, self.mock_plugin_3]

    def test_get_all_plugins(self):
        all_plugins = self.registry.get_all_plugins()
        self.assertEqual(3, len(all_plugins))
        self.assertIn(self.mock_plugin_1, all_plugins)
        self.assertIn(self.mock_plugin_2, all_plugins)

    def test_get_unique_plugin_names(self):
        unique_names = self.registry.get_unique_plugin_names()
        self.assertEqual(2, len(unique_names))
        self.assertIn('plugin1', unique_names)
        self.assertIn('plugin2', unique_names)

    def test_get_plugin(self):
        self.assertEqual(self.mock_plugin_1, self.registry.get_plugin('plugin1[inst1]-0.0.1'))

    def test_get_plugin_none(self):
        self.assertIsNone(self.registry.get_plugin('bad_name'))

    def test_get_plugins_by_system_none(self):
        plugins = self.registry.get_plugins_by_system('plugin3', '0.0.1')
        self.assertEqual(0, len(plugins))

    def test_get_plugins_by_system_one(self):
        plugins = self.registry.get_plugins_by_system('plugin1', '0.0.1')
        self.assertEqual(1, len(plugins))
        self.assertIn(self.mock_plugin_1, plugins)

    def test_get_plugins_by_system_multiple(self):
        plugins = self.registry.get_plugins_by_system('plugin2', '0.0.1')
        self.assertEqual(2, len(plugins))
        self.assertIn(self.mock_plugin_2, plugins)
        self.assertIn(self.mock_plugin_3, plugins)

    def test_remove(self):
        self.registry.remove(self.mock_plugin_1.unique_name)
        self.assertEqual(2, len(self.registry._registry))
        self.assertNotIn(self.mock_plugin_1, self.registry._registry)

    def test_remove_not_there(self):
        self.registry.remove('bad_name')
        self.assertEqual(3, len(self.registry._registry))

    def test_register_plugin(self):
        mock_plugin = Mock(system=self.fake_system_1, unique_name='plugin1[inst2]-0.0.1', instance_name='inst2',
                           status='INITIALIZING')

        self.assertEqual(3, len(self.registry._registry))
        self.registry.register_plugin(mock_plugin)
        self.assertEqual(4, len(self.registry._registry))
        self.assertIn(mock_plugin, self.registry._registry)

    def test_register_plugin_already_there(self):
        self.assertEqual(3, len(self.registry._registry))
        self.registry.register_plugin(self.mock_plugin_1)
        self.assertEqual(3, len(self.registry._registry))

    def test_plugin_exists_true(self):
        self.assertTrue(self.registry.plugin_exists(plugin_name=self.mock_plugin_1.system.name,
                                                    plugin_version=self.mock_plugin_1.system.version))

    def test_plugin_exists_false(self):
        self.assertFalse(self.registry.plugin_exists(plugin_name='bad_plugin', plugin_version='0.0.1'))

    def test_get_unique_name(self):
        self.assertEqual('echo[default]-0.0.1', self.registry.get_unique_name('echo', '0.0.1', 'default'))
