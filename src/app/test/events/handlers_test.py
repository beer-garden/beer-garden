# -*- coding: utf-8 -*-
from mock import Mock

import beer_garden
from beer_garden.events.handlers import garden_callbacks


class TestHandlers:
    def test_garden_callbacks_no_mangle(self, monkeypatch, bg_event):
        """garden_ballbacks should send a copy of event to handlers as to not mangle it"""

        def mangle(event):
            event = "mangled"
            return event

        beer_garden.application = Mock()

        for handler in [
            beer_garden.garden,
            beer_garden.plugin,
            beer_garden.requests,
            beer_garden.router,
            beer_garden.systems,
            beer_garden.scheduler,
            beer_garden.log,
            beer_garden.files,
            beer_garden.local_plugins.manager,
        ]:
            monkeypatch.setattr(handler, "handle_event", mangle)

        garden_callbacks(bg_event)
        assert bg_event != "mangled"
