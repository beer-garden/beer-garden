import json
from pathlib import Path

from box import Box

import beer_garden.log
from beer_garden.log import default_app_config


class TestLoad(object):
    def test_level(self, tmpdir):
        level = "DEBUG"

        logging_config = beer_garden.log.load(Box(level=level), force=True)

        assert logging_config == default_app_config(level)

    def test_level_and_filename(self, tmpdir):
        level = "DEBUG"
        filename = str(Path(tmpdir, "logging-config.json"))

        logging_config = beer_garden.log.load(
            Box(level=level, file=filename), force=True
        )

        assert logging_config == default_app_config(level, filename=filename)

    def test_from_file(self, tmpdir):
        config_file = Path(tmpdir, "logging-config.json")
        logging_config = {"version": 1}

        with open(config_file, "w") as f:
            f.write(json.dumps(logging_config))

        loaded_config = beer_garden.log.load(
            Box(config_file=str(config_file)), force=True
        )

        assert loaded_config == logging_config
