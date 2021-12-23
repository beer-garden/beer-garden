# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Event

from beer_garden import config
from beer_garden.db.mongo.models import CommandPublishingBlockList, Request
from beer_garden.events import event_blocklisted


class TestSendEventToParent(object):
    event = Event(
        payload_type="Request",
        payload=Request(
            system="system_test",
            command="command_test",
            namespace="test",
        ),
    )

    def config_get(self, config_name):
        return []

    @pytest.fixture()
    def command_blocklist(self):
        blocklist = CommandPublishingBlockList(
            namespace=self.event.payload.namespace,
            system=self.event.payload.system,
            command=self.event.payload.command,
        ).save()

        yield blocklist
        blocklist.delete()

    def test_command_exists_in_blocklist(self, command_blocklist, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)

        assert event_blocklisted(self.event)

    def test_command_missing_in_blocklist(self, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)

        assert not event_blocklisted(self.event)

    def test_event_not_request(self, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)
        event = Event(name="ENTRY_STARTED")

        assert not event_blocklisted(event)

    def test_can_send_event_error(self, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)
        event = Event(name="REQUEST_CREATE", error=True)

        assert event_blocklisted(event)

    def test_can_send_event_to_parent(self, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)

        assert not event_blocklisted(self.event)

    def test_can_send_event_to_parent_blocklist(self, command_blocklist, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)

        assert event_blocklisted(self.event)
