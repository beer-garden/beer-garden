# -*- coding: utf-8 -*-

import logging
import os
import pytest
from io import open

from mock import Mock

import beer_garden.local_plugins.logger as bg_logging
from beer_garden.local_plugins.logger import PluginHandler


class TestPluginHandler(object):
    def test_init_no_log_directory(self):
        fake_factory = Mock()
        PluginHandler(fake_factory, "name", log_directory=None)
        fake_factory.assert_called_with(maxBytes=10485760, backupCount=5)

    def test_init_with_log_directory(self):
        fake_factory = Mock()
        PluginHandler(fake_factory, "name", log_directory="/path")
        fake_factory.assert_called_with(
            filename=os.path.join("/path", "name.log"), maxBytes=10485760, backupCount=5
        )

    def test_getattr_true(self):
        fake_handler = Mock()
        fake_factory = Mock(return_value=fake_handler)
        handler = PluginHandler(fake_factory, "name")
        handler.foo()
        fake_handler.foo.assert_called_with()

    def test_getattr_false(self):
        fake_handler = Mock(spec=[])
        fake_factory = Mock(return_value=fake_handler)
        handler = PluginHandler(fake_factory, "name")
        with pytest.raises(AttributeError):
            handler.foo()


@pytest.fixture
def reset_foo_handlers():
    log = logging.getLogger("foo")
    if len(log.handlers) > 0:
        for h in log.handlers:
            log.removeHandler(h)


@pytest.mark.usefixtures("reset_foo_handlers")
class TestLogging(object):
    def test_get_plugin_logger_already_instantiated(self):
        log1 = bg_logging.getPluginLogger("foo")
        log2 = bg_logging.getPluginLogger("foo")
        assert log1 == log2

    @pytest.mark.parametrize(
        "log_dir,log_name,base_handler,log_level",
        [
            (None, None, logging.StreamHandler, None),
            (None, "unused", logging.StreamHandler, None),
            ("some/directory", None, PluginHandler, None),
            ("some/directory", "bar", PluginHandler, None),
            (None, None, logging.StreamHandler, logging.DEBUG),
        ],
    )
    def test_get_plugin_logger(
        self, tmpdir, log_dir, log_name, base_handler, log_level
    ):
        if log_dir:
            log_dir = os.path.join(str(tmpdir), log_dir)
            os.makedirs(log_dir)

        log = bg_logging.getPluginLogger(
            "foo", log_directory=log_dir, log_name=log_name, log_level=log_level
        )

        assert not log.propagate
        assert len(log.handlers) == 1
        assert isinstance(log.handlers[0], base_handler)
        if log_level is not None:
            assert log.handlers[0].level == log_level

        if base_handler == PluginHandler:
            if log_name:
                assert os.path.exists(os.path.join(log_dir, log_name + ".log"))
            else:
                assert os.path.exists(os.path.join(log_dir, "foo.log"))

    @pytest.mark.parametrize(
        "format_string,level,message",
        [
            (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "ERROR",
                "Hello, World",
            ),
            ("%(asctime)s - %(message)s", "WARNING", "Hello, World"),
            (None, "INFO", "Hello, World"),
            (None, "INFO", u"🍺"),
        ],
    )
    def test_formatting(self, tmpdir, caplog, format_string, level, message):
        log = bg_logging.getPluginLogger(
            "foo",
            log_directory=str(tmpdir),
            format_string=format_string,
            log_level=level,
        )

        # Pytest normally captures logs at WARNING, we need to change
        # The levels in parametrize must be higher than DEBUG!
        caplog.set_level(logging.DEBUG, logger="foo")

        log.log(getattr(logging, level), message)

        with open(os.path.join(str(tmpdir), "foo.log")) as f:
            line = f.readline().rstrip()

        if not format_string:
            assert line == message
        else:
            assert message in line

            if "name" in format_string:
                assert "foo" in line
            if "levelname" in format_string:
                assert level in line
