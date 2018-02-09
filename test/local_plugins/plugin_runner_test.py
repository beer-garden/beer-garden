import logging
import subprocess
import sys
import unittest

from mock import Mock, PropertyMock, patch, ANY
from mongoengine import DoesNotExist

from bartender.local_plugins.plugin_runner import LocalPluginRunner


class PluginRunnerTest(unittest.TestCase):

    def setUp(self):
        self.instance_mock = Mock(status='RUNNING')
        type(self.instance_mock).name = PropertyMock(return_value='default')
        self.system_mock = Mock(version='1.0.0', instances=[self.instance_mock])
        type(self.system_mock).name = PropertyMock(return_value='system_name')

        self.plugin = LocalPluginRunner('entry_point', self.system_mock, 'default',
                                        '/path/to/plugin/name',
                                        "web_host", 123, False)

    def test_init_executable_script(self):
        plugin = LocalPluginRunner('entry_point', self.system_mock, 'instance_name',
                                   '/path/to/plugin/name',
                                   "web_host", 123, False, plugin_args=['arg1', 'arg2'])
        self.assertEqual(plugin.executable, [sys.executable, 'entry_point', 'arg1', 'arg2'])

    def test_init_executable_package(self):
        plugin = LocalPluginRunner('-m package', self.system_mock, 'instance_name',
                                   '/path/to/plugin/name',
                                   "web_host", 123, False, plugin_args=['arg1', 'arg2'])
        self.assertEqual(plugin.executable, [sys.executable, '-m', 'package', 'arg1', 'arg2'])

    def test_get_status(self):
        self.assertEqual('RUNNING', self.plugin.status)
        self.assertTrue(self.instance_mock.reload.called)

    def test_get_status_2(self):
        self.instance_mock.status = 'STOPPED'
        self.assertEqual('STOPPED', self.plugin.status)
        self.assertTrue(self.instance_mock.reload.called)

    def test_get_status_error(self):
        self.instance_mock.reload.side_effect = DoesNotExist
        self.assertEqual('UNKNOWN', self.plugin.status)
        self.assertTrue(self.instance_mock.reload.called)

    def test_set_status(self):
        self.plugin.status = 'STOPPED'
        self.assertEqual('STOPPED', self.instance_mock.status)
        self.assertTrue(self.instance_mock.save.called)

    def test_set_status_error(self):
        self.instance_mock.reload.side_effect = DoesNotExist
        self.plugin.status = 'STOPPED'
        self.assertFalse(self.instance_mock.save.called)

    def test_unique_name(self):
        self.assertEqual('system_name[default]-1.0.0', self.plugin.unique_name)

    def test_generate_plugin_environment(self):
        plugin_env = {
            'BG_NAME': self.plugin.system.name,
            'BG_VERSION': self.plugin.system.version,
            'BG_INSTANCE_NAME': self.plugin.instance_name,
            'BG_PLUGIN_PATH': self.plugin.path_to_plugin,
            'BG_WEB_HOST': 'web_host',
            'BG_WEB_PORT': '123',
            'BG_SSL_ENABLED': 'False',
            'BG_URL_PREFIX': 'None',
            'BG_CA_VERIFY': 'True',
            'BG_CA_CERT': 'None'
        }

        self.assertDictEqual(plugin_env, self.plugin._generate_plugin_environment())

    def test_generate_plugin_environment_no_copy_extra_bg_env(self):
        generated_env = self.plugin._generate_plugin_environment()
        self.assertNotIn('BG_foo', generated_env)
        self.assertIn('BG_NAME', generated_env)

    def test_generate_plugin_environment_with_additional_environment(self):
        self.plugin.environment = {'FOO': 'BAR'}
        plugin_env = self.plugin._generate_plugin_environment()
        self.assertEqual(plugin_env.get('FOO'), 'BAR')

    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment',
           Mock(return_value=1))
    @patch('bartender.local_plugins.plugin_runner.Thread', Mock())
    @patch('bartender.local_plugins.plugin_runner.subprocess.Popen')
    def test_process_creation(self, process_mock):
        stdout_mock = Mock(readline=Mock(return_value=b""))
        process_mock.return_value = Mock(poll=Mock(return_value="Not None"), stdout=stdout_mock)

        self.plugin.run()
        process_mock.assert_called_with(self.plugin.executable, env=1, bufsize=0,
                                        stderr=subprocess.STDOUT,
                                        stdout=subprocess.PIPE, preexec_fn=ANY,
                                        cwd=self.plugin.path_to_plugin)

    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment',
           Mock())
    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner.stopped',
           Mock(return_value=True))
    @patch('bartender.local_plugins.plugin_runner.subprocess.Popen')
    @patch('bartender.local_plugins.plugin_runner.sleep')
    @patch('bartender.local_plugins.plugin_runner.Thread')
    def test_run_plugin_io_thread_successful_stop(self, thread_mock, sleep_mock, process_mock):
        self.plugin.logger.error = Mock()
        fake_thread = Mock()
        thread_mock.return_value = fake_thread
        process_mock.return_value.poll.side_effect = [None, 0, 0]

        self.plugin.run()
        self.assertEqual(0, self.plugin.logger.error.call_count)
        thread_mock.assert_called_with(name=self.plugin.unique_name+'_io_thread',
                                       target=self.plugin._check_io)
        sleep_mock.assert_called_once_with(0.1)
        fake_thread.start.assert_called_with()
        fake_thread.join.assert_called_once_with()

    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment',
           Mock())
    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner.stopped',
           Mock(return_value=False))
    @patch('bartender.local_plugins.plugin_runner.subprocess.Popen')
    @patch('bartender.local_plugins.plugin_runner.sleep')
    @patch('bartender.local_plugins.plugin_runner.Thread')
    def test_run_plugin_io_thread_bad_stop(self, thread_mock, sleep_mock, process_mock):
        self.plugin.logger.error = Mock()
        fake_thread = Mock()
        thread_mock.return_value = fake_thread
        process_mock.return_value.poll.side_effect = [None, 1, 1]

        self.plugin.run()
        self.plugin.logger.error.assert_called()
        thread_mock.assert_called_with(name=self.plugin.unique_name+'_io_thread',
                                       target=self.plugin._check_io)
        sleep_mock.assert_called_once_with(0.1)
        fake_thread.start.assert_called_with()
        fake_thread.join.assert_called_once_with()

    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment',
           Mock(return_value={}))
    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner.stopped',
           Mock(return_value=True))
    @patch('bartender.local_plugins.plugin_runner.subprocess.Popen')
    @patch('bartender.local_plugins.plugin_runner.Thread')
    def test_check_io_no_custom_logger_used(self, thread_mock, process_mock):
        stdout_mock = Mock(name='stdout mock', readline=Mock(side_effect=[b"no logger", b""]))
        process_mock.return_value = Mock(name='process mock', poll=Mock(return_value=0),
                                         stdout=stdout_mock)
        thread_mock.return_value = Mock(name='thread mock', join=self.plugin._check_io)
        self.plugin.logger = Mock()

        self.plugin.run()
        self.plugin.logger.info.assert_any_call('no logger'.rstrip())

    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment',
           Mock(return_value={}))
    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner.stopped',
           Mock(return_value=True))
    @patch('bartender.local_plugins.plugin_runner.subprocess.Popen')
    @patch('bartender.local_plugins.plugin_runner.Thread')
    def test_check_io_custom_logger_being_used(self, thread_mock, process_mock):
        stdout_mock = Mock(name='stdout mock', readline=Mock(
            side_effect=[
                b"ERROR: this is my error logger", b"INFO: this is my info logger", b""]))
        process_mock.return_value = Mock(name='process mock', poll=Mock(return_value=0),
                                         stdout=stdout_mock)
        thread_mock.return_value = Mock(name='thread mock', join=self.plugin._check_io)
        self.plugin.logger = Mock()

        self.plugin.run()
        self.plugin.logger.log.assert_any_call(logging.ERROR, "ERROR: this is my error logger")
        self.plugin.logger.log.assert_any_call(logging.INFO, "INFO: this is my info logger")

    def test_check_io_multiple_calls(self):
        stdout_mock = Mock(name='stdout mock', readline=Mock(
            side_effect=[
                b"ERROR: this is my error logger", b"INFO: this is my info logger", b"", b""]))
        check_io_mock = Mock(wraps=self.plugin._check_io)
        logger_mock = Mock()
        self.plugin.process = Mock(name='process mock', poll=Mock(side_effect=[None, 0, 0]),
                                   stdout=stdout_mock)
        self.plugin._check_io = check_io_mock
        self.plugin.logger = logger_mock

        self.plugin._check_io()
        self.assertLess(1, check_io_mock.call_count)
        logger_mock.log.assert_any_call(logging.ERROR, "ERROR: this is my error logger")
        logger_mock.log.assert_any_call(logging.INFO, "INFO: this is my info logger")

    @patch('bartender.local_plugins.plugin_runner.subprocess.Popen',
           Mock(side_effect=ValueError('error_message')))
    @patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment',
           Mock())
    def test_run_call_throw_exception(self):
        self.plugin.logger.error = Mock()
        self.plugin.run()
        self.plugin.logger.error.assert_called_with('error_message')

    def test_kill_process(self):
        self.plugin.process = Mock(poll=Mock(return_value=None))
        self.plugin.kill()
        self.assertEqual(self.plugin.process.kill.call_count, 1)

    def test_kill_process_dead(self):
        self.plugin.process = Mock(poll=Mock(return_value="dead"))
        self.plugin.kill()
        self.assertEqual(self.plugin.process.kill.call_count, 0)
