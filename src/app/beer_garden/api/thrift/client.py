import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import brewtils.thrift
from thriftpy2.rpc import make_client

pool = ThreadPoolExecutor(50)


class FakeClient(object):
    def __getattr__(self, _api):
        return partial(self, _api)

    def __call__(self, *args, **kwargs):
        from beer_garden.api.thrift.handler import BartenderHandler
        return asyncio.get_event_loop().run_in_executor(
            pool, getattr(BartenderHandler, args[0]), *args[1:]
        )


class ThriftClient(object):
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
        # self._client = await make_aio_client(
        #     brewtils.thrift.bg_thrift.BartenderBackend,
        #     host=self._host,
        #     port=self._port,
        #     socket_timeout=13000,
        # )
        # return self._client
        return FakeClient()

    async def __aexit__(self, exc_type, exc, tb):
        # self._client.close()
        pass
