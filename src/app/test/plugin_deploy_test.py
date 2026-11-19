import os
import shutil
import tarfile
from io import BytesIO
from pathlib import Path

import pytest
from brewtils.models import Runner
from mock import Mock

import beer_garden.plugin_deploy
from beer_garden import config
from beer_garden.db.mongo.models import Instance, System
from beer_garden.errors import PluginValidationError
from beer_garden.plugin_deploy import (
    _clean_existing,
    _get_target_folder_path,
    _migrate_conf,
    _stage_files_tarfile,
    _stage_files_zip,
    _validate_extracted_folder,
    deploy_plugin,
)


@pytest.fixture
def plugin_dir(tmp_path):

    plugin_folder = tmp_path / "plugins"
    plugin_folder.mkdir()

    config._CONFIG = {"plugin": {"local": {"directory": str(plugin_folder.resolve())}}}

    yield plugin_folder


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test to ensure a clean state."""
    System.drop_collection()


class TestPluginDeploy(object):

    def zip_directory(self, directory: Path, target_directory: Path):
        # Target directory is the folder to drop the zip into
        file = shutil.make_archive(target_directory / "archive", "zip", directory)
        return Path(file)

    def targz_directory(self, directory: Path, target_path: Path):
        # Target Path must be full file path
        with tarfile.open(target_path, "w:gz") as tar:
            tar.add(directory, arcname=os.path.basename(directory))
        return target_path

    def make_plugin_folder(self, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)

        original_conf = folder / "beer.conf"
        original_conf.write_text("PLUGIN_ENTRY")

        return folder

    def test_migrate_conf(self, tmp_path):
        original_dir = self.make_plugin_folder(tmp_path / "original")

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        _migrate_conf(str(original_dir.resolve()), target_dir)

        migrated_file = target_dir / "beer.conf"

        assert migrated_file.exists()

    def test_migrate_conf_missing(self, tmp_path):
        original_dir = tmp_path / "original"
        original_dir.mkdir()

        target_dir = tmp_path / "target"
        target_dir.mkdir()

        _migrate_conf(str(original_dir.resolve()), target_dir)

        migrated_file = target_dir / "beer.conf"

        assert not migrated_file.exists()

    def test_get_target_folder(self, plugin_dir):

        assert _get_target_folder_path("/test") == "/test"
        assert _get_target_folder_path("test") == str((plugin_dir / "test").resolve())

    def test_validate_extracted_raise_exception(self, tmp_path):

        folder = tmp_path / "folder"
        folder.mkdir()

        self.make_plugin_folder(folder / "sub_dir" / "nested")

        with pytest.raises(PluginValidationError, match="Unable to find beer.conf"):
            _validate_extracted_folder(folder)

    def test_validate_extracted_sub_folder(self, tmp_path):

        folder = tmp_path / "folder"
        folder.mkdir()

        sub_folder = self.make_plugin_folder(folder / "sub_dir")

        target_folder = _validate_extracted_folder(folder)

        assert target_folder == sub_folder

    def test_validate_extracted(self, tmp_path):

        folder = self.make_plugin_folder(tmp_path / "folder")

        target_folder = _validate_extracted_folder(folder)

        assert target_folder == folder

    def test_stage_zip(self, tmp_path):
        tmp_folder = self.make_plugin_folder(tmp_path / "tmp")

        source_folder = self.make_plugin_folder(tmp_path / "source")
        compressed_files = tmp_path / "compressed"
        compressed_files.mkdir()
        zipped_file = self.zip_directory(source_folder, compressed_files)
        with open(zipped_file, "rb") as fh:
            # Read the full file contents into the BytesIO buffer
            file_buffer = BytesIO(fh.read())

        target_path = _stage_files_zip(
            file_bytes=file_buffer,
            target_folder="target",
            tmpdir=str(tmp_folder.resolve()),
        )

        assert target_path == tmp_folder / "target"

    def test_stage_tarfile(self, tmp_path):
        tmp_folder = self.make_plugin_folder(tmp_path / "tmp")

        source_folder = self.make_plugin_folder(tmp_path / "source")
        compressed_files = tmp_path / "compressed.tar.gz"

        tar_file = self.targz_directory(source_folder, compressed_files)
        with open(tar_file, "rb") as fh:
            # Read the full file contents into the BytesIO buffer
            file_buffer = BytesIO(fh.read())

        target_path = _stage_files_tarfile(
            file_bytes=file_buffer,
            target_folder="target",
            tmpdir=str(tmp_folder.resolve()),
        )

        assert target_path == tmp_folder / "target"

    def test_cleanup_existing_folder(self, plugin_dir, monkeypatch):
        monkeypatch.setattr(beer_garden.plugin_deploy, "runners", Mock(return_value=[]))

        plugin_folder = plugin_dir / "target"
        plugin_folder.mkdir()

        assert plugin_folder.exists()

        _clean_existing("target")

        assert not plugin_folder.exists()

    def test_cleanup_existing_purge_system(self, plugin_dir, monkeypatch):
        purge_system_mock = Mock()
        monkeypatch.setattr(
            beer_garden.plugin_deploy,
            "runners",
            Mock(return_value=[Runner(path="target", id="1234")]),
        )
        monkeypatch.setattr(
            beer_garden.plugin_deploy, "purge_system", purge_system_mock
        )

        target_system = System(
            name="a",
            version="1.0.0",
            namespace="a",
            instances=[Instance(metadata={"runner_id": "1234"})],
        ).save()
        plugin_folder = plugin_dir / "target"
        plugin_folder.mkdir()

        _clean_existing("target")

        assert purge_system_mock.call_args[1]["system"].id == str(target_system.id)

    def test_extract_zip(self, tmp_path, plugin_dir, monkeypatch):
        monkeypatch.setattr(beer_garden.plugin_deploy, "runners", Mock(return_value=[]))
        monkeypatch.setattr(beer_garden.plugin_deploy, "rescan", Mock())

        source_folder = self.make_plugin_folder(tmp_path / "source")
        compressed_files = tmp_path / "compressed"
        compressed_files.mkdir()
        zipped_file = self.zip_directory(source_folder, compressed_files)
        with open(zipped_file, "rb") as fh:
            # Read the full file contents into the BytesIO buffer
            file_buffer = BytesIO(fh.read())

        deploy_plugin("target", file_bytes=file_buffer, migrate_conf=False, is_zip=True)

        target_config = plugin_dir / "target" / "beer.conf"

        assert target_config.exists()

    def test_extract_targz(self, tmp_path, plugin_dir, monkeypatch):
        monkeypatch.setattr(beer_garden.plugin_deploy, "runners", Mock(return_value=[]))
        monkeypatch.setattr(beer_garden.plugin_deploy, "rescan", Mock())

        source_folder = self.make_plugin_folder(tmp_path / "source")
        compressed_files = tmp_path / "compressed.tar.gz"

        tar_file = self.targz_directory(source_folder, compressed_files)
        with open(tar_file, "rb") as fh:
            # Read the full file contents into the BytesIO buffer
            file_buffer = BytesIO(fh.read())

        deploy_plugin(
            "target", file_bytes=file_buffer, migrate_conf=False, is_tarfile=True
        )

        target_config = plugin_dir / "target" / "beer.conf"

        assert target_config.exists()
