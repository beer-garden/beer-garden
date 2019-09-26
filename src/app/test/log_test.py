import json
import logging.config
from pathlib import Path

import pytest
from mock import Mock

import beer_garden.log
from beer_garden.log import default_app_config


class TestLoad(object):
    @pytest.fixture(autouse=True)
    def patch_global_logging(self, monkeypatch):
        """The config needs to not change or else it messes up subsequent tests"""
        monkeypatch.setattr(logging.config, "dictConfig", Mock())

    def test_level(self, tmpdir):
        level = "DEBUG"

        beer_garden.log.load({"level": level}, force=True)

        assert beer_garden.log._LOGGING_CONFIG == default_app_config(level)

    def test_level_and_filename(self, tmpdir):
        level = "DEBUG"
        filename = str(Path(tmpdir, "logging-config.json"))

        beer_garden.log.load({"level": level, "file": filename}, force=True)

        assert beer_garden.log._LOGGING_CONFIG == default_app_config(
            level, filename=filename
        )

    def test_from_file(self, tmpdir):
        config_file = Path(tmpdir, "logging-config.json")
        logging_config = {"version": 1}

        with open(config_file, "w") as f:
            f.write(json.dumps(logging_config))

        beer_garden.log.load({"config_file": str(config_file)}, force=True)

        assert beer_garden.log._LOGGING_CONFIG == logging_config
