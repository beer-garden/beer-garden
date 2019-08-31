from thriftpy2.rpc import make_aio_client

import beer_garden.brew_view
import brewtils.thrift


class ThriftClient:
    async def __aenter__(self):
        self._client = await make_aio_client(
            brewtils.thrift.bg_thrift.BartenderBackend,
            host=beer_garden.brew_view.config.backend.host,
            port=beer_garden.brew_view.config.backend.port,
            socket_timeout=beer_garden.brew_view.config.backend.socket_timeout,
        )
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        self._client.close()
