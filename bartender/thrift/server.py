import logging
from concurrent.futures import wait, ThreadPoolExecutor, ALL_COMPLETED
from threading import Event

from thriftpy2.server import TThreadedServer
from thriftpy2.thrift import TProcessor
from thriftpy2.transport import TServerSocket, TSSLServerSocket

import bg_utils
from brewtils.stoppable_thread import StoppableThread
import bartender


class BartenderThriftServer(TThreadedServer, StoppableThread):
    """Thrift server that uses a ThreadPoolExecutor to process requests"""

    # Amount of time (in seconds) after shutdown requested to wait for workers to finish processing
    WORKER_TIMEOUT = 5

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.display_name = "Thrift Server"
        self.pool = ThreadPoolExecutor(max_workers=bartender.config.thrift.max_workers)
        self.futures = set()
        self.finished = Event()

        StoppableThread.__init__(
            self, logger=self.logger, name=kwargs.pop("name", "ThriftPyServer")
        )
        TThreadedServer.__init__(self, *args, **kwargs)

    def run(self):
        self.logger.info(self.display_name + " is started")
        self.serve()

        # We could still be waiting on worker threads to finish -
        # we need another event to tell when REALLY stopped
        self.finished.wait(timeout=self.WORKER_TIMEOUT + 1)
        self.logger.info(self.display_name + " is stopped")

    def stop(self):
        # Mark the thread as stopping
        StoppableThread.stop(self)

        # Close the socket - this will kick us out of the self.trans.accept() call with an exception
        self.trans.close()

        # Wait some amount of time for all the futures to complete
        futures_status = wait(
            self.futures, timeout=self.WORKER_TIMEOUT, return_when=ALL_COMPLETED
        )

        # If there are still workers remaining after the timeout then we remove references to them.
        # We need to do this because workers are daemons but concurrent.futures.thread adds a
        # hook to join all workers with no timeout when shutting down. So any hung worker would
        # prevent the application from shutting down.
        if futures_status.not_done:
            self.logger.warning(
                "There were still unfinished worker "
                "threads even after waiting, about to orphan them"
            )

            import concurrent.futures.thread

            self.pool._threads.clear()
            concurrent.futures.thread._threads_queues.clear()

        # Let run() know that we've made our attempt to wait
        # for all the workers and now it's time to die
        self.finished.set()

    def serve(self):
        self.trans.listen()

        while not self.stopped():
            try:
                trans_input = self.trans.accept()

                future = self.pool.submit(self.handle, trans_input)
                self.futures.add(future)
                future.add_done_callback(lambda x: self.futures.remove(x))
            except OSError as ex:
                if not self.stopped() or ex.errno != 22:
                    self.logger.exception(ex)
            except Exception as ex:
                self.logger.exception(ex)


class WrappedTProcessor(TProcessor):
    """Processor that fails gracefully if a handler method raises an unexpected exception"""

    def __init__(self, default_exception_name, default_exception_cls, *args, **kwargs):
        super(WrappedTProcessor, self).__init__(*args, **kwargs)
        self.default_exception_name = default_exception_name
        self.default_exception_cls = default_exception_cls
        self.logger = logging.getLogger(__name__)

    def handle_exception(self, e, result):
        try:
            return super(WrappedTProcessor, self).handle_exception(e, result)
        except Exception as ex:
            self.logger.exception(
                "Uncaught exception occurred during thrift execution: %s", ex
            )
            setattr(
                result,
                self.default_exception_name,
                self.default_exception_cls(
                    str(ex) or "No message was found on the raised exception."
                ),
            )


def make_server(
    service, handler, host="127.0.0.1", port=9090, client_timeout=None, cert_file=None
):
    """Factory method to create a BartenderThriftServer"""

    if cert_file:
        server_socket = TSSLServerSocket(
            host=host, port=port, client_timeout=client_timeout, certfile=cert_file
        )
    else:
        server_socket = TServerSocket(
            host=host, port=port, client_timeout=client_timeout
        )

    return BartenderThriftServer(
        WrappedTProcessor("baseEx", bg_utils.bg_thrift.BaseException, service, handler),
        server_socket,
    )
