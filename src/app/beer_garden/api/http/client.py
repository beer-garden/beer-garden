import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

pool = ThreadPoolExecutor(50)


class ExecutorClient(object):
    def __getattr__(self, _api):
        return partial(self, _api)

    def __call__(self, *args, **kwargs):
        from beer_garden.api.thrift.handler import BartenderHandler

        return asyncio.get_event_loop().run_in_executor(
            pool, getattr(BartenderHandler, args[0]), *args[1:]
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass
