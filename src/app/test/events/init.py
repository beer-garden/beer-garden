# -*- coding: utf-8 -*-
import pytest
from mock import Mock

from beer_garden import config
from beer_garden.db.mongo.models import CommandPublishingBlackList
from beer_garden.events import event_blacklisted


@pytest.fixture
def model_mocks(monkeypatch):
    event_mock = Mock()

    event_mock.__name__ = "event"

    return {
        "event": event_mock,
    }


class TestCommandBlackList(object):
    namespace = "test"
    system = "system_test"
    command = "command_test"

    def config_get(self, config_name):
        return []

    @pytest.fixture()
    def command_black_list(self):
        black_list = CommandPublishingBlackList(
            namespace=self.namespace, system=self.system, command=self.command
        ).save()

        yield black_list
        black_list.delete()

    def test_exists(self, model_mocks, command_black_list, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)
        model_mocks["event"].payload_type = "Request"
        model_mocks["event"].payload.namespace = self.namespace
        model_mocks["event"].payload.system = self.system
        model_mocks["event"].payload.command = self.command

        assert event_blacklisted(model_mocks["event"])

    def test_missing(self, model_mocks, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)
        model_mocks["event"].payload_type = "Request"

        assert not event_blacklisted(model_mocks["event"])

    def test_payload_type_not_request(self, model_mocks, monkeypatch):
        monkeypatch.setattr(config, "get", self.config_get)
        model_mocks["event"].payload_type = "Garden_create"

        assert not event_blacklisted(model_mocks["event"])
