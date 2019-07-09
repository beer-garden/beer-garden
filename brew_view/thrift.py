from thriftpy2.rpc import make_aio_client

import bg_utils
import brew_view


class ThriftClient:
    async def __aenter__(self):
        self._client = await make_aio_client(
            bg_utils.bg_thrift.BartenderBackend,
            host=brew_view.config.backend.host,
            port=brew_view.config.backend.port,
            socket_timeout=brew_view.config.backend.socket_timeout,
        )
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        self._client.close()
