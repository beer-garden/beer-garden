# -*- coding: utf-8 -*-
from thriftpy2.rpc import make_aio_client, make_client

import beer_garden.api.thrift


class ThriftClient(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def __enter__(self):
        self._client = make_client(
            beer_garden.api.thrift.bg_thrift.BartenderBackend,
            host=self._host,
            port=self._port,
            timeout=13000,
        )
        return self._client

    def __exit__(self, exc_type, exc, tb):
        self._client.close()

    async def __aenter__(self):
        self._client = await make_aio_client(
            beer_garden.api.thrift.bg_thrift.BartenderBackend,
            # These hard coded values should not exist after the refactor.
            host="0.0.0.0",
            port=9090,
            socket_timeout=13000,
        )
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        self._client.close()
