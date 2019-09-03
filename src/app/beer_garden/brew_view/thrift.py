from thriftpy2.rpc import make_aio_client

import brewtils.thrift


class ThriftClient:
    async def __aenter__(self):
        self._client = await make_aio_client(
            brewtils.thrift.bg_thrift.BartenderBackend,
            # These hard coded values should not exist after the refactor.
            host="0.0.0.0",
            port=9090,
            socket_timeout=13000,
        )
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        self._client.close()
