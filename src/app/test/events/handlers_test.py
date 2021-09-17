# -*- coding: utf-8 -*-
import beer_garden.events.handlers


class TestHandlers:
    def test_garden_callbacks_no_mangle(self, monkeypatch, bg_event):
        """garden_ballbacks should send a copy of event to handlers as to not not mangle it"""

        def mangle(event):
            event = "mangled"

        handlers = [
            #beer_garden.application.handle_event,
            beer_garden.garden,
            beer_garden.plugin,
            beer_garden.requests,
            beer_garden.router,
            beer_garden.systems,
            beer_garden.scheduler,
            beer_garden.log,
            beer_garden.files,
            beer_garden.local_plugins.manager,
        ]

        for handler in handlers:
            monkeypatch.setattr(handler, "handle_event", mangle)

        beer_garden.events.handlers.garden_callbacks(bg_event)
        assert bg_event != "mangled"
