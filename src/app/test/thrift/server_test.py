import unittest
from concurrent.futures import Future

from mock import ANY, Mock, patch

from bartender.thrift.server import BartenderThriftServer, make_server
from thriftpy2.transport import TServerSocket, TSSLServerSocket


class ThriftServerTest(unittest.TestCase):
    def setUp(self):
        self.timeout_mock = Mock()

        self.processor_mock = Mock()
        self.trans_mock = Mock()
        self.pool_mock = Mock()

        with patch("bartender.config") as config_mock:
            config_mock.thrift.max_workers = 25
            self.server = BartenderThriftServer(self.processor_mock, self.trans_mock)
            self.server.pool = self.pool_mock

    @patch("bartender.thrift.server.BartenderThriftServer.serve")
    def test_run(self, serve_mock):
        finished_mock = Mock()
        self.server.finished = finished_mock

        self.server.run()
        serve_mock.assert_called_once_with()
        self.assertTrue(finished_mock.wait.called)

    def test_stop_no_futures(self):
        logger_mock = Mock()
        self.server.logger = logger_mock

        self.server.stop()
        self.assertTrue(self.server.finished.is_set())
        self.assertFalse(logger_mock.warning.called)

    def test_stop_outstanding_futures(self):
        logger_mock = Mock()
        self.server.logger = logger_mock

        self.server.futures.add(Future())
        self.server.WORKER_TIMEOUT = 0

        self.server.stop()
        self.assertTrue(logger_mock.warning.called)
        self.assertTrue(self.pool_mock._threads.clear.called)
        self.assertTrue(self.server.finished.is_set())

    @patch(
        "bartender.thrift.server.BartenderThriftServer.stopped", Mock(return_value=True)
    )
    def test_serve_already_stopped(self):
        self.server.serve()
        self.trans_mock.listen.assert_called_once_with()
        self.assertFalse(self.trans_mock.accept.called)

    @patch(
        "bartender.thrift.server.BartenderThriftServer.stopped",
        Mock(side_effect=[False, True]),
    )
    def test_serve(self):
        trans_input = Mock()
        self.trans_mock.accept.return_value = trans_input

        logger_mock = Mock()
        self.server.logger = logger_mock

        self.server.serve()
        self.trans_mock.accept.assert_called_once_with()
        self.pool_mock.submit.assert_called_once_with(ANY, trans_input)
        self.assertFalse(logger_mock.exception.called)

    @patch(
        "bartender.thrift.server.BartenderThriftServer.stopped",
        Mock(side_effect=[False, True]),
    )
    def test_serve_exception(self):
        self.trans_mock.accept.side_effect = ValueError

        logger_mock = Mock()
        self.server.logger = logger_mock

        self.server.serve()
        self.trans_mock.accept.assert_called_once_with()
        self.assertTrue(logger_mock.exception.called)

    @patch(
        "bartender.thrift.server.BartenderThriftServer.stopped",
        Mock(side_effect=[False, True, True]),
    )
    def test_serve_exit_exception(self):
        error = OSError()
        error.errno = 22
        self.trans_mock.accept.side_effect = error

        logger_mock = Mock()
        self.server.logger = logger_mock

        self.server.serve()
        self.trans_mock.accept.assert_called_once_with()
        self.assertFalse(logger_mock.exception.called)


class MakeServerTest(unittest.TestCase):
    @patch("bartender.config", Mock(thrift=Mock(max_workers=1)))
    def test_make_server_no_cert(self):
        server = make_server(Mock(), Mock())
        self.assertIsInstance(server.trans, TServerSocket)
        self.assertNotIsInstance(server.trans, TSSLServerSocket)

    @patch("bartender.config", Mock(thrift=Mock(max_workers=1)))
    @patch("thriftpy2.transport.sslsocket.os", Mock())
    @patch("thriftpy2.transport.sslsocket.create_thriftpy_context", Mock())
    def test_make_server_with_cert(self):
        server = make_server(Mock(), Mock(), cert_file=Mock())
        self.assertIsInstance(server.trans, TSSLServerSocket)
