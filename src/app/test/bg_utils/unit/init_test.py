from __future__ import unicode_literals

import json
import os
from io import open

import pytest
from mock import patch, Mock
from ruamel import yaml
from yapconf import YapconfSpec


@pytest.fixture
def spec():
    return YapconfSpec(
        {
            "log": {
                "type": "dict",
                "items": {
                    "config_file": {
                        "type": "str",
                        "description": "Path to a logging config file.",
                        "required": False,
                        "cli_short_name": "l",
                        "previous_names": ["log_config"],
                        "alt_env_names": ["LOG_CONFIG"],
                    },
                    "file": {
                        "type": "str",
                        "description": "File you would like the application to log to",
                        "required": False,
                        "previous_names": ["log_file"],
                    },
                    "level": {
                        "type": "str",
                        "description": "Log level for the application",
                        "default": "INFO",
                        "choices": [
                            "DEBUG",
                            "INFO",
                            "WARN",
                            "WARNING",
                            "ERROR",
                            "CRITICAL",
                        ],
                        "previous_names": ["log_level"],
                    },
                },
            },
            "configuration": {
                "type": "dict",
                "bootstrap": True,
                "items": {
                    "file": {
                        "required": False,
                        "bootstrap": True,
                        "cli_short_name": "c",
                    },
                    "type": {
                        "required": False,
                        "bootstrap": True,
                        "cli_short_name": "t",
                    },
                },
            },
        }
    )


@pytest.fixture
def old_config():
    """Represent an un-migrated config with previous default values."""
    return {
        "log_config": None,
        "log_file": None,
        "log_level": "INFO",
        "configuration": {"type": "json"},
    }


@pytest.fixture
def new_config():
    """Represents a up-to-date config with all new values."""
    return {"log": {"config_file": None, "file": None, "level": "INFO"}}


class TestSafeMigrate(object):
    def test_success(self, tmpdir, spec, old_config, new_config):
        old_filename = os.path.join(str(tmpdir), "config.json")
        old_config["configuration"]["file"] = old_filename
        cli_args = {"configuration": {"file": old_filename, "type": "json"}}

        with open(old_filename, "w") as f:
            f.write(json.dumps(old_config, ensure_ascii=False))

        generated_config = bg_utils.load_application_config(spec, cli_args)
        assert generated_config.log.level == "INFO"

        with open(old_filename) as f:
            new_config_value = json.load(f)

        assert new_config_value == new_config
        assert len(os.listdir(str(tmpdir))) == 2

    def test_no_change(self, tmpdir, spec, new_config):
        config_file = os.path.join(str(tmpdir), "config.yaml")
        cli_args = {"configuration": {"file": config_file}}

        with open(config_file, "w") as f:
            yaml.safe_dump(new_config, f, default_flow_style=False, encoding="utf-8")

        generated_config = bg_utils.load_application_config(spec, cli_args)
        assert generated_config.log.level == "INFO"

        with open(config_file) as f:
            new_config_value = yaml.safe_load(f)

        assert new_config_value == new_config
        assert len(os.listdir(str(tmpdir))) == 1

    def test_migration_failure(self, capsys, tmpdir, spec, old_config):
        old_filename = os.path.join(str(tmpdir), "config.json")
        cli_args = {"configuration": {"file": old_filename, "type": "json"}}

        spec.migrate_config_file = Mock(side_effect=ValueError)

        with open(old_filename, "w") as f:
            f.write(json.dumps(old_config, ensure_ascii=False))

        generated_config = bg_utils.load_application_config(spec, cli_args)

        # Make sure we printed something
        assert capsys.readouterr().err

        # If the migration fails, we should still have a single unchanged JSON file.
        assert len(os.listdir(str(tmpdir))) == 1
        with open(old_filename) as f:
            new_config_value = json.load(f)
        assert new_config_value == old_config

        # And the values should be unchanged
        assert generated_config.log.level == "INFO"

    def test_rename_failure(self, capsys, tmpdir, spec, old_config):
        old_filename = os.path.join(str(tmpdir), "config.json")
        cli_args = {"configuration": {"file": old_filename, "type": "json"}}

        with open(old_filename, "w") as f:
            f.write(json.dumps(old_config, ensure_ascii=False))

        with patch("os.rename", Mock(side_effect=ValueError)):
            generated_config = bg_utils.load_application_config(spec, cli_args)

        # Make sure we printed something
        assert capsys.readouterr().err

        assert generated_config.log.level == "INFO"

        # Both the tmp file and the old JSON should still be there.
        assert len(os.listdir(str(tmpdir))) == 2
        with open(old_filename + ".tmp") as f:
            yaml.safe_load(f)

        # The loaded config should be the JSON file.
        with open(old_filename) as f:
            new_config_value = json.load(f)

        assert new_config_value == old_config

    def test_catastrophe(self, capsys, tmpdir, spec, old_config):
        old_filename = os.path.join(str(tmpdir), "config.json")
        cli_args = {"configuration": {"file": old_filename, "type": "json"}}

        with open(old_filename, "w") as f:
            f.write(json.dumps(old_config, ensure_ascii=False))

        with patch("os.rename", Mock(side_effect=[Mock(), ValueError])):
            with pytest.raises(ValueError):
                bg_utils.load_application_config(spec, cli_args)

        # Make sure we printed something
        assert capsys.readouterr().err

        # Both the tmp file and the old JSON should still be there.
        assert len(os.listdir(str(tmpdir))) == 2
