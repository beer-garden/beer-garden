import logging
import string
import subprocess
from random import choice

import pytest
import sys
from mock import Mock, call

from beer_garden.local_plugins.runner import ProcessRunner


@pytest.fixture
def runner(tmp_path):
    return ProcessRunner(
        runner_id="".join([choice(string.ascii_letters) for _ in range(10)]),
        process_args=["python", "-m", "echo"],
        process_cwd=tmp_path,
        process_env={},
        capture_streams=False,
    )


@pytest.mark.skip
class TestPluginRunner(object):
    @pytest.mark.parametrize(
        "entry_point,expected",
        [
            ("entry_point", [sys.executable, "entry_point", "arg1", "arg2"]),
            ("-m package", [sys.executable, "-m", "package", "arg1", "arg2"]),
        ],
    )
    def test_init_entry_point(self, system_mock, entry_point, expected):
        plugin = ProcessRunner(
            entry_point,
            system_mock,
            "instance_name",
            "/path/to/plugin/name",
            "web_host",
            123,
            False,
            plugin_args=["arg1", "arg2"],
        )
        assert plugin.executable == expected

    def test_unique_name(self, plugin):
        assert plugin.unique_name == "system_name[default]-1.0.0"

    def test_plugin_loggers_levels(self, plugin, system_mock):
        # We have to null out the handlers, otherwise we will end up
        # using a cached handler.
        plugin.unformatted_logger.handlers = []
        runner = ProcessRunner(
            "entry_point",
            system_mock,
            "default",
            "/path/to/plugin/name",
            "web_host",
            123,
            False,
            log_level=logging.DEBUG,
        )
        assert runner.logger.level == logging.getLogger(__name__).getEffectiveLevel()
        assert runner.unformatted_logger.level == logging.DEBUG

    def test_generate_plugin_environment(self, plugin):
        plugin_env = {
            "BG_NAME": plugin.system.name,
            "BG_VERSION": plugin.system.version,
            "BG_INSTANCE_NAME": plugin.instance_name,
            "BG_PLUGIN_PATH": plugin.path_to_plugin,
            "BG_WEB_HOST": "web_host",
            "BG_WEB_PORT": "123",
            "BG_SSL_ENABLED": "False",
            "BG_URL_PREFIX": "None",
            "BG_CA_VERIFY": "True",
            "BG_CA_CERT": "None",
            "BG_USERNAME": "None",
            "BG_PASSWORD": "None",
            "BG_LOG_LEVEL": "INFO",
        }

        assert plugin._generate_plugin_environment() == plugin_env

    def test_generate_plugin_environment_no_copy_extra_bg_env(self, plugin):
        generated_env = plugin._generate_plugin_environment()
        assert "BG_foo" not in generated_env
        assert "BG_NAME" in generated_env

    def test_generate_plugin_environment_with_additional_environment(self, plugin):
        plugin.environment = {"FOO": "BAR"}
        plugin_env = plugin._generate_plugin_environment()
        assert plugin_env.get("FOO") == "BAR"

    @pytest.mark.parametrize(
        "process_poll,stopped,error_called",
        [
            ([None, 0, 0], True, False),  # Successful stop
            ([None, 1, 1], False, True),  # Bad stop
        ],
    )
    def test_run_plugin_io_thread_stop(
        self, mocker, plugin, process_poll, stopped, error_called
    ):
        thread_mock = mocker.patch("beer_garden.local_plugins.plugin_runner.Thread")
        sleep_mock = mocker.patch("beer_garden.local_plugins.plugin_runner.sleep")
        process_mock = mocker.patch(
            "beer_garden.local_plugins.plugin_runner.subprocess.Popen"
        )
        plugin.stopped = Mock(return_value=stopped)

        plugin.logger.error = Mock()
        fake_thread = Mock()
        thread_mock.return_value = fake_thread
        process_mock.return_value.poll.side_effect = process_poll

        plugin.run()
        assert plugin.logger.error.called == error_called
        assert fake_thread.start.called
        assert fake_thread.join.called
        sleep_mock.assert_called_once_with(0.1)


@pytest.mark.skip
class TestCheckIo(object):
    @pytest.mark.parametrize(
        "stdout,stderr,logger_calls",
        [
            (
                ["print to stdout", "INFO: hello", "ERROR: world", ""],
                ["print to stderr", "WARNING: - on stderr", ""],
                {
                    "unformatted_logger": [
                        call(logging.INFO, "print to stdout"),
                        call(logging.ERROR, "print to stderr"),
                        call(logging.INFO, "INFO: hello"),
                        call(logging.WARNING, "WARNING: - on stderr"),
                        call(logging.ERROR, "ERROR: world"),
                    ]
                },
            )
        ],
    )
    def test_check_io(self, mocker, plugin, stdout, stderr, logger_calls):
        """Ensure output coming from the subprocess is logged correctly

        The plugin_output param specifies what is returned from each call
        to ``readline``. It should end with ``""``.

        The logger_and_calls param should be a tuple. The first item should
        specify which logger should be used to handle that output, and the
        second item should be a ``call`` describing how the logger was called
        """
        process_mock = mocker.patch(
            "beer_garden.local_plugins.plugin_runner.subprocess.Popen"
        )
        plugin.stopped = Mock(return_value=True)

        stdout_mock = Mock(name="stdout mock", readline=Mock(side_effect=stdout))
        stderr_mock = Mock(name="stderr mock", readline=Mock(side_effect=stderr))

        process_mock.return_value = Mock(
            name="process mock",
            poll=Mock(return_value=0),
            stdout=stdout_mock,
            stderr=stderr_mock,
        )

        plugin.unformatted_logger = Mock(name="unformatted")

        plugin.run()

        for logger_name, logger_calls in logger_calls.items():
            for logger_call in logger_calls:
                assert logger_call in getattr(plugin, logger_name).log.mock_calls

    def test_check_io_multiple_calls(self, plugin):
        stdout_mock = Mock(
            name="stdout mock",
            readline=Mock(
                side_effect=[
                    "ERROR: this is my error logger",
                    "INFO: this is my info logger",
                    "",
                    "",
                ]
            ),
        )
        check_io_mock = Mock(wraps=plugin._check_io)
        plugin.process = Mock(
            name="process mock", poll=Mock(side_effect=[None, 0, 0]), stdout=stdout_mock
        )
        plugin._check_io = check_io_mock

        plugin._check_io(stdout_mock, logging.INFO)
        assert check_io_mock.call_count > 1


class TestRun(object):
    def test_exception(self, caplog, monkeypatch, runner):
        monkeypatch.setattr(
            subprocess, "Popen", Mock(side_effect=ValueError("error_message"))
        )

        with caplog.at_level(logging.ERROR):
            runner.run()

        assert len(caplog.messages) == 1
        assert "error_message" in caplog.messages[0]


class TestKill(object):
    def test_alive(self, runner):
        runner.process = Mock(poll=Mock(return_value=None))
        runner.kill()
        assert runner.process.kill.called

    def test_dead(self, runner):
        runner.process = Mock(poll=Mock(return_value="dead"))
        runner.kill()
        assert not runner.process.kill.called
