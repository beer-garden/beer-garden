# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Event
from brewtils.test.comparable import assert_event_equal

from beer_garden.events.processors import FanoutProcessor, PrettyPrinter


class TestFanoutProcessor(object):
    @pytest.fixture
    def event(self):
        return Event(name="mock", payload="Hello!")

    @pytest.fixture
    def processor(self):
        return FanoutProcessor()

    def test_add_event(self, processor, bg_event):
        processor.put(bg_event)

        assert_event_equal(processor._queue.get(), bg_event)

    def test_register_listener(self, processor):
        processor.register(PrettyPrinter(stream=None), start=False)

        assert len(processor._processors) == 1
