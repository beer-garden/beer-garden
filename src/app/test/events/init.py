# -*- coding: utf-8 -*-
import pytest
from brewtils.models import Event

from beer_garden import config
from beer_garden.db.mongo.models import CommandPublishingBlackList, Request
from beer_garden.events import can_send_event_to_parent, event_blacklisted


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
    def command_black_list(self):
        black_list = CommandPublishingBlackList(
            namespace=self.event.payload.namespace,
            system=self.event.payload.system,
            command=self.event.payload.command,
        ).save()

        yield black_list
        black_list.delete()

    def test_command_exists_in_blacklist(self, command_black_list, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)

        assert event_blacklisted(self.event)

    def test_command_missing_in_blacklist(self, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)

        assert not event_blacklisted(self.event)

    def test_event_not_request(self, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)
        event = Event(name="ENTRY_STARTED")

        assert not event_blacklisted(event)

    def test_can_send_event_error(self, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)
        event = Event(name="REQUEST_CREATE", error=True)

        assert not can_send_event_to_parent(event)

    def test_can_send_event_to_parent(self, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)

        assert can_send_event_to_parent(self.event)

    def test_can_send_event_to_parent_blacklisted(
        self, command_black_list, monkeypatch
    ):
        monkeypatch.setattr(config, "get", self.config_get)

        assert not can_send_event_to_parent(self.event)
