# -*- coding: utf-8 -*-
import os

import pytest
import yapconf
from mock import Mock
from ruamel import yaml
from yapconf import YapconfSpec

import beer_garden.config


class TestLoadConfig(object):
    def test_no_config_file(self):
        beer_garden.config.load([], force=True)
        spec = YapconfSpec(beer_garden.config._SPECIFICATION)
        assert beer_garden.config._CONFIG == spec.defaults


class TestGenerateConfig(object):
    def test_correctness(self, tmpdir):
        config_file = os.path.join(str(tmpdir), "config.yaml")
        logging_config_file = os.path.join(str(tmpdir), "logging.json")

        beer_garden.config.generate(["-c", config_file, "-l", logging_config_file])

        spec = YapconfSpec(beer_garden.config._SPECIFICATION)
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
    def test_create_file(self, tmpdir, file_type):
        filename = os.path.join(str(tmpdir), "temp." + file_type)
        beer_garden.config.generate(["-c", filename, "-t", file_type])

        assert os.path.getsize(filename) > 0

    @pytest.mark.parametrize("file_type", ["json", "yaml"])
    def test_file_infer_type(self, tmpdir, file_type):
        filename = os.path.join(str(tmpdir), "temp." + file_type)
        beer_garden.config.generate(["-c", filename])

        assert os.path.getsize(filename) > 0

    @pytest.mark.parametrize("file_type", ["json", "yaml"])
    def test_stdout(self, capsys, file_type):
        beer_garden.config.generate(["-t", file_type])

        # Just make sure we printed something
        assert capsys.readouterr().out

    def test_omit_bootstrap(self, tmpdir):
        filename = os.path.join(str(tmpdir), "temp.yaml")
        beer_garden.config.generate(["-c", filename])

        with open(filename) as f:
            config = yaml.safe_load(f)

        assert "log" in config
        assert "configuration" not in config


class TestUpdateConfig(object):
    @pytest.mark.parametrize(
        "extension,file_type", [("json", "json"), ("yaml", "yaml"), ("yml", "yaml")]
    )
    def test_success(self, tmpdir, extension, file_type):
        config_file = os.path.join(str(tmpdir), "config." + extension)

        beer_garden.config.generate(["-c", config_file])
        beer_garden.config.migrate(["-c", config_file])

        assert os.path.exists(config_file)

    @pytest.mark.parametrize(
        "current_type,new_type", [("json", "yaml"), ("yaml", "json")]
    )
    def test_change_type(self, tmpdir, current_type, new_type):
        current_config = os.path.join(str(tmpdir), "config." + current_type)
        new_config = os.path.join(str(tmpdir), "config." + new_type)

        beer_garden.config.generate(["-c", current_config])
        beer_garden.config.migrate(["-c", current_config, "-t", new_type])

        assert os.path.exists(new_config)
        assert not os.path.exists(current_config)

    def test_change_type_error(self, monkeypatch, tmpdir):
        config_file = os.path.join(str(tmpdir), "config.json")
        beer_garden.config.generate(["-c", config_file])

        error_mock = Mock(side_effect=ValueError)
        monkeypatch.setattr(yapconf.spec.YapconfSpec, "migrate_config_file", error_mock)

        with pytest.raises(ValueError):
            beer_garden.config.migrate(["-c", config_file, "-t", "yaml"])

        assert os.path.exists(config_file)

    def test_no_file_specified(self):
        with pytest.raises(SystemExit):
            beer_garden.config.migrate([])


class TestConfigGet(object):
    def test_gets(self):
        beer_garden.config.load([], force=True)
        amq = beer_garden.config.get("amq")
        assert amq.host == "localhost"
        assert amq["host"] == "localhost"
        assert beer_garden.config.get("publish_hostname") == "localhost"
        assert beer_garden.config.get("amq.host") == "localhost"
        assert beer_garden.config.get("INVALID_KEY") is None
        assert beer_garden.config.get("") is None
