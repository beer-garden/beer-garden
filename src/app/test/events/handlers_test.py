# -*- coding: utf-8 -*-
from mock import Mock
from beer_garden.events.handlers import garden_callbacks

class TestHandlers:
    def test_garden_callbacks_no_mangle(self, monkeypatch, bg_event):
        """garden_ballbacks should send a copy of event to handlers as to not mangle it"""

        def mangle(event):
            event = "mangled"

        beer_garden.events.handlers.event_handlers = Mock()
        for handler in beer_garden.events.handlers.event_handlers:
            monkeypatch.setattr(handler, "handle_event", mangle)

        garden_callbacks(bg_event)
        assert bg_event != "mangled"
