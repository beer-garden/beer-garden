# -*- coding: utf-8 -*-
from yapconf import YapconfSpec

from beer_garden import config


class TestLoadConfig(object):
    def test_no_config_file(self):
        config.load([], force=True)
        spec = YapconfSpec(config._SPECIFICATION)
        assert config._CONFIG == spec.defaults


class TestConfigGet(object):
    def test_gets(self):
        config.load([], force=True)
        amq = config.get("amq")
        assert amq.host == "localhost"
        assert amq["host"] == "localhost"
        assert config.get("publish_hostname") == "localhost"
        assert config.get("amq.host") == "localhost"
        assert config.get("INVALID_KEY") is None
        assert config.get("") is None
