import logging
import subprocess
import sys
import pytest

from mock import Mock, PropertyMock, call, patch, ANY
from mongoengine import DoesNotExist

from bartender.local_plugins.plugin_runner import LocalPluginRunner


@pytest.fixture
def instance_mock():
    inst_mock = Mock(status='RUNNING')
    type(inst_mock).name = PropertyMock(return_value='default')
    return inst_mock


@pytest.fixture
def system_mock(instance_mock):
    sys_mock = Mock(version='1.0.0', instances=[instance_mock])
    type(sys_mock).name = PropertyMock(return_value='system_name')
    return sys_mock


@pytest.fixture
def plugin(system_mock):
    return LocalPluginRunner('entry_point', system_mock, 'default',
                             '/path/to/plugin/name', 'web_host', 123, False)

class TestPluginRunner(object):

    @pytest.mark.parametrize('entry_point,expected', [
        ('entry_point', [sys.executable, 'entry_point', 'arg1', 'arg2']),
        ('-m package', [sys.executable, '-m', 'package', 'arg1', 'arg2']),
    ])
    def test_init_entry_point(self, system_mock, entry_point, expected):
        plugin = LocalPluginRunner(entry_point, system_mock, 'instance_name',
                                   '/path/to/plugin/name', "web_host", 123,
                                   False, plugin_args=['arg1', 'arg2'])
        assert plugin.executable == expected

    def test_unique_name(self, plugin):
        assert plugin.unique_name == 'system_name[default]-1.0.0'

    def test_get_status(self, plugin, instance_mock):
        assert plugin.status == 'RUNNING'
        assert instance_mock.reload.called

    def test_get_status_error(self, plugin, instance_mock):
        instance_mock.reload.side_effect = DoesNotExist
        assert plugin.status == 'UNKNOWN'
        assert instance_mock.reload.called

    def test_set_status(self, plugin, instance_mock):
        plugin.status = 'STOPPED'
        assert plugin.status == 'STOPPED'
        assert instance_mock.save.called

    def test_set_status_error(self, plugin, instance_mock):
        instance_mock.reload.side_effect = DoesNotExist
        plugin.status = 'STOPPED'
        assert not instance_mock.save.called

    def test_generate_plugin_environment(self, plugin):
        plugin_env = {
            'BG_NAME': plugin.system.name,
            'BG_VERSION': plugin.system.version,
            'BG_INSTANCE_NAME': plugin.instance_name,
            'BG_PLUGIN_PATH': plugin.path_to_plugin,
            'BG_WEB_HOST': 'web_host',
            'BG_WEB_PORT': '123',
            'BG_SSL_ENABLED': 'False',
            'BG_URL_PREFIX': 'None',
            'BG_CA_VERIFY': 'True',
            'BG_CA_CERT': 'None'
        }

        assert plugin._generate_plugin_environment() == plugin_env

    def test_generate_plugin_environment_no_copy_extra_bg_env(self, plugin):
        generated_env = plugin._generate_plugin_environment()
        assert 'BG_foo' not in generated_env
        assert 'BG_NAME' in generated_env

    def test_generate_plugin_environment_with_additional_environment(self, plugin):
        plugin.environment = {'FOO': 'BAR'}
        plugin_env = plugin._generate_plugin_environment()
        assert plugin_env.get('FOO') == 'BAR'

    def test_process_creation(self, mocker, plugin):
        mocker.patch('bartender.local_plugins.plugin_runner.Thread')
        env_mock = mocker.patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment')
        process_mock = mocker.patch('bartender.local_plugins.plugin_runner.subprocess.Popen')

        stdout_mock = Mock(readline=Mock(return_value=b""))
        process_mock.return_value = Mock(poll=Mock(return_value="Not None"), stdout=stdout_mock)

        plugin.run()
        process_mock.assert_called_with(plugin.executable, env=env_mock(),
                                        bufsize=0, stderr=subprocess.STDOUT,
                                        stdout=subprocess.PIPE, preexec_fn=ANY,
                                        cwd=plugin.path_to_plugin)

    @pytest.mark.parametrize('process_poll,stopped,error_called', [
        ([None, 0, 0], True, False),  # Successful stop
        ([None, 1, 1], False, True),  # Bad stop
    ])
    def test_run_plugin_io_thread_stop(self, mocker, plugin, process_poll, stopped, error_called):
        mocker.patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment')
        thread_mock = mocker.patch('bartender.local_plugins.plugin_runner.Thread')
        sleep_mock = mocker.patch('bartender.local_plugins.plugin_runner.sleep')
        process_mock = mocker.patch('bartender.local_plugins.plugin_runner.subprocess.Popen')
        stopped_mock = mocker.patch('bartender.local_plugins.plugin_runner.LocalPluginRunner.stopped',
                                    Mock(return_value=stopped))

        plugin.logger.error = Mock()
        fake_thread = Mock()
        thread_mock.return_value = fake_thread
        process_mock.return_value.poll.side_effect = process_poll

        plugin.run()
        assert plugin.logger.error.called == error_called
        assert fake_thread.start.called
        assert fake_thread.join.called
        thread_mock.assert_called_with(name=plugin.unique_name+'_io_thread',
                                       target=plugin._check_io)
        sleep_mock.assert_called_once_with(0.1)

    @pytest.mark.parametrize('plugin_output,logger_calls', [
        ([b"no logger", b""],
            [call(logging.INFO, 'no logger')]
        ),
        ([b"ERROR: this is my error logger", b"INFO: this is my info logger", b""],
            [
                call(logging.ERROR, 'ERROR: this is my error logger'),
                call(logging.INFO, 'INFO: this is my info logger'),
            ]
        ),
    ])
    def test_check_io(self, mocker, plugin, plugin_output, logger_calls):
        mocker.patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment',
                     Mock(return_value={}))
        mocker.patch('bartender.local_plugins.plugin_runner.LocalPluginRunner.stopped',
                     Mock(return_value=True))
        thread_mock = mocker.patch('bartender.local_plugins.plugin_runner.Thread')
        process_mock = mocker.patch('bartender.local_plugins.plugin_runner.subprocess.Popen')

        stdout_mock = Mock(name='stdout mock', readline=Mock(side_effect=plugin_output))
        process_mock.return_value = Mock(name='process mock', poll=Mock(return_value=0),
                                         stdout=stdout_mock)
        thread_mock.return_value = Mock(name='thread mock', join=plugin._check_io)
        plugin.logger = Mock()

        plugin.run()
        plugin.logger.log.assert_has_calls(logger_calls)

    def test_check_io_multiple_calls(self, plugin):
        stdout_mock = Mock(name='stdout mock', readline=Mock(
            side_effect=[
                b"ERROR: this is my error logger", b"INFO: this is my info logger", b"", b""]))
        check_io_mock = Mock(wraps=plugin._check_io)
        logger_mock = Mock()
        plugin.process = Mock(name='process mock', poll=Mock(side_effect=[None, 0, 0]),
                              stdout=stdout_mock)
        plugin._check_io = check_io_mock
        plugin.logger = logger_mock

        plugin._check_io()
        assert check_io_mock.call_count > 1

    def test_run_call_throw_exception(self, mocker, plugin):
        mocker.patch('bartender.local_plugins.plugin_runner.subprocess.Popen',
            Mock(side_effect=ValueError('error_message')))
        mocker.patch('bartender.local_plugins.plugin_runner.LocalPluginRunner._generate_plugin_environment')

        plugin.logger.error = Mock()
        plugin.run()
        plugin.logger.error.assert_called_with('error_message')

    def test_kill_process(self, plugin):
        plugin.process = Mock(poll=Mock(return_value=None))
        plugin.kill()
        assert plugin.process.kill.called

    def test_kill_process_dead(self, plugin):
        plugin.process = Mock(poll=Mock(return_value="dead"))
        plugin.kill()
        assert not plugin.process.kill.called
