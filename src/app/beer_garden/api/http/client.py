# -*- coding: utf-8 -*-
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial

import beer_garden.api


class ExecutorClient(object):

    pool = ThreadPoolExecutor(50)

    def __getattr__(self, _api):
        return partial(self, _api)

    def __call__(self, *args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(
            self.pool, partial(getattr(beer_garden.api, args[0]), *args[1:], **kwargs)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


client = ExecutorClient()
