from thriftpy2.rpc import make_client

import bg_utils


class ThriftClient:
    def __enter__(self):
        self._client = make_client(
            bg_utils.bg_thrift.BartenderBackend,
            # TODO - Obviously this needs to not be hardcoded
            host="localhost",
            port=9091,
            timeout=13000,
        )
        return self._client

    def __exit__(self, exc_type, exc, tb):
        self._client.close()
