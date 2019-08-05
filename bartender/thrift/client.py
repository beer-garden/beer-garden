from thriftpy2.rpc import make_client

import brewtils.thrift


class ThriftClient:
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def __enter__(self):
        self._client = make_client(
            brewtils.thrift.bg_thrift.BartenderBackend,
            host=self._host,
            port=self._port,
            timeout=13000,
        )
        return self._client

    def __exit__(self, exc_type, exc, tb):
        self._client.close()
