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


class TestBgUtils(object):
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

    @pytest.mark.parametrize(
        "file_name,file_type,expected_type",
        [
            (None, None, "yaml"),
            (None, "yaml", "yaml"),
            (None, "json", "json"),
            ("file", None, "yaml"),
            ("file", "yaml", "yaml"),
            ("file", "json", "json"),
            ("file.yaml", None, "yaml"),
            ("file.blah", None, "yaml"),
            ("file.json", None, "json"),
            ("file.yaml", "yaml", "yaml"),
            ("file.yaml", "json", "json"),
            ("file.json", "yaml", "yaml"),
            ("file.json", "json", "json"),
        ],
    )
    def test_get_config_type(self, file_name, file_type, expected_type):
        config = Box({"configuration": {"file": file_name, "type": file_type}})
        assert bg_utils._get_config_type(config) == expected_type


class TestGenerateConfig(object):
    def test_correctness(self, tmpdir, spec):
        config_file = os.path.join(str(tmpdir), "config.yaml")
        logging_config_file = os.path.join(str(tmpdir), "logging.json")

        bg_utils.generate_config_file(
            spec, ["-c", config_file, "-l", logging_config_file]
        )

        spec.add_source(label="config_file", source_type="yaml", filename=config_file)
        config = spec.load_config("config_file")

        # Defaults from spec
        assert config.log.file is None
        assert config.log.level == "INFO"

        # Value passed in
        assert config.log.config_file == logging_config_file

        # Ensure that bootstrap items were not written to file
        assert config.configuration.file is None
        assert config.configuration.type is None

        with open(config_file) as f:
            yaml_config = yaml.safe_load(f)
        assert "configuration" not in yaml_config

    @pytest.mark.parametrize("file_type", ["json", "yaml"])
    def test_create_file(self, spec, tmpdir, file_type):
        filename = os.path.join(str(tmpdir), "temp." + file_type)
        bg_utils.generate_config_file(spec, ["-c", filename, "-t", file_type])

        assert os.path.getsize(filename) > 0

    @pytest.mark.parametrize("file_type", ["json", "yaml"])
    def test_file_infer_type(self, spec, tmpdir, file_type):
        filename = os.path.join(str(tmpdir), "temp." + file_type)
        bg_utils.generate_config_file(spec, ["-c", filename])

        assert os.path.getsize(filename) > 0

    @pytest.mark.parametrize("file_type", ["json", "yaml"])
    def test_stdout(self, spec, capsys, file_type):
        bg_utils.generate_config_file(spec, ["-t", file_type])

        # Just make sure we printed something
        assert capsys.readouterr().out

    def test_omit_bootstrap(self, spec, tmpdir):
        filename = os.path.join(str(tmpdir), "temp.yaml")
        bg_utils.generate_config_file(spec, ["-c", filename])

        with open(filename) as f:
            config = yaml.safe_load(f)

        assert "log" in config
        assert "configuration" not in config


class TestUpdateConfig(object):
    @pytest.mark.parametrize(
        "extension,file_type", [("json", "json"), ("yaml", "yaml"), ("yml", "yaml")]
    )
    def test_success(self, monkeypatch, spec, extension, file_type):
        migrate_mock = Mock()
        spec.migrate_config_file = migrate_mock
        spec.update_defaults = Mock()

        remove_mock = Mock()
        monkeypatch.setattr(os, "remove", remove_mock)

        bg_utils.update_config_file(spec, ["-c", "/path/to/config." + extension])

        expected = Box(
            {
                "log_file": None,
                "log_level": "INFO",
                "log_config": None,
                "configuration": {"file": "/path/to/config." + extension},
            }
        )
        migrate_mock.assert_called_once_with(
            expected.configuration.file,
            current_file_type=file_type,
            output_file_name=expected.configuration.file,
            output_file_type=file_type,
            update_defaults=True,
            include_bootstrap=False,
        )
        assert remove_mock.called is False

    @pytest.mark.parametrize(
        "current_type,new_type", [("json", "yaml"), ("yaml", "json")]
    )
    def test_change_type(self, monkeypatch, spec, current_type, new_type):
        migrate_mock = Mock()
        spec.migrate_config_file = migrate_mock
        spec.update_defaults = Mock()

        remove_mock = Mock()
        monkeypatch.setattr(os, "remove", remove_mock)

        bg_utils.update_config_file(
            spec, ["-c", "/path/to/config." + current_type, "-t", new_type]
        )

        migrate_mock.assert_called_once_with(
            "/path/to/config." + current_type,
            current_file_type=current_type,
            output_file_name="/path/to/config." + new_type,
            output_file_type=new_type,
            update_defaults=True,
            include_bootstrap=False,
        )
        remove_mock.assert_called_once_with("/path/to/config." + current_type)

    def test_change_type_error(self, monkeypatch, spec):
        migrate_mock = Mock(side_effect=ValueError)
        spec.migrate_config_file = migrate_mock
        spec.update_defaults = Mock()

        remove_mock = Mock()
        monkeypatch.setattr(os, "remove", remove_mock)

        with pytest.raises(ValueError):
            bg_utils.update_config_file(
                spec, ["-c", "/path/to/config.json", "-t", "yaml"]
            )
        assert remove_mock.called is False

    def test_no_file_specified(self, spec):
        migrate_mock = Mock()
        spec.migrate_config_file = migrate_mock

        with pytest.raises(SystemExit):
            bg_utils.update_config_file(spec, [])

        assert migrate_mock.called is False


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
