import logging
import os
import pytest
from io import open

from mock import Mock

import bartender.local_plugins.logger as bg_logging
from bartender.local_plugins.logger import PluginHandler


class TestPluginHandler(object):

    def test_init_no_log_directory(self):
        fake_factory = Mock()
        PluginHandler(fake_factory, 'name', log_directory=None)
        fake_factory.assert_called_with(maxBytes=10485760, backupCount=5)

    def test_init_with_log_directory(self):
        fake_factory = Mock()
        PluginHandler(fake_factory, 'name', log_directory="/path")
        fake_factory.assert_called_with(filename=os.path.join("/path", "name.log"),
                                        maxBytes=10485760, backupCount=5)

    def test_getattr_true(self):
        fake_handler = Mock()
        fake_factory = Mock(return_value=fake_handler)
        handler = PluginHandler(fake_factory, 'name')
        handler.foo()
        fake_handler.foo.assert_called_with()

    def test_getattr_false(self):
        fake_handler = Mock(spec=[])
        fake_factory = Mock(return_value=fake_handler)
        handler = PluginHandler(fake_factory, 'name')
        with pytest.raises(AttributeError):
            handler.foo()


@pytest.fixture
def reset_foo_handlers():
    log = logging.getLogger('foo')
    if len(log.handlers) > 0:
        for h in log.handlers:
            log.removeHandler(h)


@pytest.mark.usefixtures('reset_foo_handlers')
class TestLogging(object):

    def test_get_plugin_logger_already_instantiated(self):
        log1 = bg_logging.getPluginLogger('foo', formatted=False)
        log2 = bg_logging.getPluginLogger('foo', formatted=False)
        assert log1 == log2

    @pytest.mark.parametrize('log_dir,log_name,base_handler', [
        (None, None, logging.StreamHandler),
        (None, 'unused', logging.StreamHandler),
        ('some/directory', None, PluginHandler),
        ('some/directory', 'bar', PluginHandler),
    ])
    def test_get_plugin_logger(self, tmpdir, log_dir, log_name, base_handler):
        if log_dir:
            log_dir = os.path.join(str(tmpdir), log_dir)
            os.makedirs(log_dir)

        log = bg_logging.getPluginLogger('foo', log_directory=log_dir,
                                         log_name=log_name)

        assert not log.propagate
        assert len(log.handlers) == 1
        assert isinstance(log.handlers[0], base_handler)

        if base_handler == PluginHandler:
            if log_name:
                assert os.path.exists(os.path.join(log_dir, log_name+'.log'))
            else:
                assert os.path.exists(os.path.join(log_dir, 'foo.log'))

    @pytest.mark.parametrize('formatted,level,message', [
        (True, 'ERROR', 'this should be formatted'),
        (False, 'INFO', 'this should be unformatted'),
        ('timestamp', 'WARNING', 'this should have only a timestamp'),
    ])
    def test_formatting(self, tmpdir, caplog, formatted, level, message):
        log = bg_logging.getPluginLogger('foo', log_directory=str(tmpdir),
                                         formatted=formatted)

        # Pytest normally captures logs at WARNING, we need to change
        # The levels in parametrize must be higher than DEBUG!
        caplog.set_level(logging.DEBUG, logger="foo")

        log.log(getattr(logging, level), message)

        with open(os.path.join(str(tmpdir), 'foo.log')) as f:
            line = f.readline().rstrip()

        if formatted is True:
            assert 'foo' in line
            assert level in line
            assert message in line
            assert not line.startswith(message)
        elif formatted == 'timestamp':
            assert level not in line
            assert message in line
            assert not line.startswith(message)
        else:
            assert line == message
