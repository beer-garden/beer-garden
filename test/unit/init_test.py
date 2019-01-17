from __future__ import unicode_literals

import json
import os
from io import open
from ruamel import yaml

import pytest
from box import Box
from mock import patch, Mock
from yapconf import YapconfSpec

import bg_utils
import bg_utils.mongo.models


class TestBgUtils(object):
    @pytest.fixture
    def spec(self):
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
    def old_config(self):
        """Represent an un-migrated config with previous default values."""
        return {
            "log_config": None,
            "log_file": None,
            "log_level": "INFO",
            "configuration": {"type": "json"},
        }

    @pytest.fixture
    def new_config(self):
        """Represents a up-to-date config with all new values."""
        return {
            "log": {"config_file": None, "file": None, "level": "WARN"},
            "configuration": {"type": "yaml"},
        }

    def test_parse_args(self, spec):
        cli_args = [
            "--log-config-file",
            "/path/to/log/config",
            "--log-file",
            "/path/to/log/file",
            "--log-level",
            "INFO",
        ]
        data = bg_utils.parse_args(
            spec, ["log.config_file", "log.file", "log.level"], cli_args
        )
        assert data == {
            "log": {
                "config_file": "/path/to/log/config",
                "file": "/path/to/log/file",
                "level": "INFO",
            }
        }

    def test_generate_config(self, spec):
        config = bg_utils._generate_config(spec, ["-c", "/path/to/config"])
        assert config.log.file is None
        assert config.log.config_file is None
        assert config.log.level == "INFO"
        assert config.configuration.file == "/path/to/config"

    @pytest.mark.parametrize("file_type", ["json", "yaml"])
    def test_generate_config_file(self, spec, tmpdir, file_type):
        filename = os.path.join(str(tmpdir), "temp." + file_type)
        bg_utils.generate_config_file(spec, ["-c", filename, "-t", file_type])

        # For this case we don't tell generate the file type
        filename2 = os.path.join(str(tmpdir), "temp2." + file_type)
        bg_utils.generate_config_file(spec, ["-c", filename2])

        assert os.path.getsize(filename) > 0
        assert os.path.getsize(filename2) > 0

    @pytest.mark.parametrize("file_type", ["json", "yaml"])
    def test_generate_config_file_print(self, spec, capsys, file_type):
        bg_utils.generate_config_file(spec, ["-t", file_type])

        # Just make sure we printed something
        assert capsys.readouterr().out

    @pytest.mark.parametrize("file_type", ["json", "yaml"])
    def test_update_config(self, spec, file_type):
        spec.update_defaults = Mock()
        spec.migrate_config_file = Mock()
        bg_utils.update_config_file(spec, ["-c", "/path/to/config." + file_type])

        expected = Box(
            {
                "log_file": None,
                "log_level": "INFO",
                "log_config": None,
                "configuration": {"file": "/path/to/config." + file_type},
            }
        )
        spec.migrate_config_file.assert_called_once_with(
            expected.configuration.file,
            update_defaults=True,
            current_file_type=file_type,
            output_file_type=file_type,
        )

    def test_update_config_no_config_specified(self, spec):
        spec.migrate_config_file = Mock()
        with pytest.raises(SystemExit):
            bg_utils.update_config_file(spec, [])

        assert spec.migrate_config_file.called is False

    @patch("bg_utils.open")
    def test_generate_logging_config(self, open_mock, spec):
        fake_file = Mock()
        fake_file.__exit__ = Mock()
        fake_file.__enter__ = Mock(return_value=fake_file)
        open_mock.return_value = fake_file
        generated_config = {"foo": "bar"}
        config_generator = Mock(return_value=generated_config)

        logging_config = bg_utils.generate_logging_config_file(
            spec, config_generator, ["--log-config-file", "/path/to/log/config"]
        )
        assert logging_config == generated_config
        assert open_mock.called is True

    @patch("bg_utils.open")
    def test_generate_logging_config_no_file(self, open_mock, spec):
        generated_config = {"foo": "bar"}
        config_generator = Mock(return_value=generated_config)

        logging_config = bg_utils.generate_logging_config_file(
            spec, config_generator, []
        )
        config_generator.assert_called_with("INFO", None)
        assert logging_config == generated_config
        assert open_mock.called is False

    @pytest.mark.parametrize(
        "config",
        [
            # (file extension, file type, file contents)
            ("yaml", "yaml", "log_level: DEBUG"),
            ("yaml", None, "log_level: DEBUG"),
            ("json", None, '{"log_level": "DEBUG"}'),
            ("json", "json", '{"log_level": "DEBUG"}'),
            ("", "yaml", "log_level: DEBUG"),
            ("", None, "log_level: DEBUG"),
        ],
    )
    def test_setup_with_config_file(self, tmpdir, spec, config):

        config_file = os.path.join(str(tmpdir), "config." + config[0])
        cli_args = {"configuration": {"file": config_file, "type": config[1]}}

        with open(config_file, "w") as f:
            f.write(config[2])

        generated_config = bg_utils.load_application_config(spec, cli_args)
        assert generated_config.log.level == "DEBUG"
        assert len(spec.sources) == 3

    def test_load_application_config_no_file_given(self, spec):
        config = bg_utils.load_application_config(spec, {})
        assert type(config) == Box
        assert len(spec.sources) == 2

    @patch("bg_utils.logging.config.dictConfig")
    def test_setup_application_logging_no_log_config(self, config_mock):
        app_config = Box({"log": {"config_file": None}})
        bg_utils.setup_application_logging(app_config, {})
        config_mock.assert_called_with({})

    @patch("bg_utils.open")
    @patch("json.load")
    @patch("bg_utils.logging.config.dictConfig")
    def test_setup_application_logging_from_file(
        self, config_mock, json_mock, open_mock
    ):
        fake_file = Mock()
        fake_file.__exit__ = Mock()
        fake_file.__enter__ = Mock(return_value=fake_file)
        open_mock.return_value = fake_file
        fake_config = {"foo": "bar"}
        json_mock.return_value = fake_config
        app_config = Mock(log_config="/path/to/log/config")
        bg_utils.setup_application_logging(app_config, {})
        config_mock.assert_called_with({"foo": "bar"})

    def test_generate_logging_config_no_mock(self, tmpdir, spec):
        config_path = tmpdir.join("logging-config.json")
        generated_config = {"foo": "bar"}
        config_generator = Mock(return_value=generated_config)

        logging_config = bg_utils.generate_logging_config_file(
            spec, config_generator, ["--log-config", str(config_path)]
        )

        assert logging_config == generated_config

    def test_safe_migrate_migration_failure(self, tmpdir, spec, old_config):
        old_filename = os.path.join(str(tmpdir), "config.json")
        old_config["configuration"]["file"] = old_filename
        cli_args = {"configuration": {"file": old_filename, "type": "json"}}

        with open(old_filename, "w") as f:
            f.write(json.dumps(old_config, ensure_ascii=False))

        spec.migrate_config_file = Mock(side_effect=ValueError)
        generated_config = bg_utils.load_application_config(spec, cli_args)
        assert generated_config.log.level == "INFO"

        # If the migration fails, we should still have JSON file.
        with open(old_filename) as f:
            new_config_value = json.load(f)

        assert len(os.listdir(str(tmpdir))) == 1
        assert new_config_value == old_config

    def test_safe_migrate_initial_rename_failure(self, tmpdir, spec, old_config):
        old_filename = os.path.join(str(tmpdir), "config.json")
        old_config["configuration"]["file"] = old_filename
        cli_args = {"configuration": {"file": old_filename, "type": "json"}}

        with open(old_filename, "w") as f:
            f.write(json.dumps(old_config, ensure_ascii=False))

        with patch("os.rename", Mock(side_effect=ValueError)):
            generated_config = bg_utils.load_application_config(spec, cli_args)

        assert generated_config.log.level == "INFO"

        # The tmp file should still be there.
        with open(old_filename + ".tmp") as f:
            yaml.safe_load(f)

        # However the loaded config, should be a JSON file.
        with open(old_filename) as f:
            new_config_value = json.load(f)

        assert len(os.listdir(str(tmpdir))) == 2
        assert new_config_value == old_config

    def test_safe_migrate_catastrophe(self, tmpdir, spec, old_config):
        old_filename = os.path.join(str(tmpdir), "config.json")
        old_config["configuration"]["file"] = old_filename
        cli_args = {"configuration": {"file": old_filename, "type": "json"}}

        with open(old_filename, "w") as f:
            f.write(json.dumps(old_config, ensure_ascii=False))

        with patch("os.rename", Mock(side_effect=[Mock(), ValueError])):
            with pytest.raises(ValueError):
                bg_utils.load_application_config(spec, cli_args)
        assert len(os.listdir(str(tmpdir))) == 2

    def test_safe_migrate_success(self, tmpdir, spec, old_config):
        old_filename = os.path.join(str(tmpdir), "config.json")
        old_config["configuration"]["file"] = old_filename
        cli_args = {"configuration": {"file": old_filename, "type": "json"}}
        expected_new_config = {
            "log": {"config_file": None, "file": None, "level": "INFO"},
            "configuration": {"file": old_filename, "type": "json"},
        }

        with open(old_filename, "w") as f:
            f.write(json.dumps(old_config, ensure_ascii=False))

        generated_config = bg_utils.load_application_config(spec, cli_args)
        assert generated_config.log.level == "INFO"

        with open(old_filename) as f:
            new_config_value = json.load(f)

        assert new_config_value == expected_new_config
        assert len(os.listdir(str(tmpdir))) == 2

    def test_safe_migrate_no_change(self, tmpdir, spec, new_config):
        filename = os.path.join(str(tmpdir), "config.yaml")
        new_config["configuration"]["file"] = filename
        cli_args = {"configuration": {"file": filename, "type": "yaml"}}

        with open(filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(new_config, f, default_flow_style=False, encoding="utf-8")

        generated_config = bg_utils.load_application_config(spec, cli_args)
        assert generated_config.to_dict() == new_config

        assert len(os.listdir(str(tmpdir))) == 1
