import brewtils.thrift
from thriftpy2.rpc import make_client, make_aio_client


class ThriftClient:
    # These hard coded values should not exist after the refactor.
    def __init__(self, host="0.0.0.0", port=9090):
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

    async def __aenter__(self):
        self._client = await make_aio_client(
            brewtils.thrift.bg_thrift.BartenderBackend,
            host=self._host,
            port=self._port,
            socket_timeout=13000,
        )
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        self._client.close()
