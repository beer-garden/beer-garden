import shutil
import tarfile
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

from brewtils.models import System

import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.errors import PluginValidationError
from beer_garden.files import fetch_file
from beer_garden.local_plugins.manager import rescan, runners
from beer_garden.systems import purge_system


def deploy_plugin(
    target_folder: str,
    file_bytes: BytesIO = None,
    file_id: str = None,
    migrate_conf: bool = False,
    is_zip: bool = False,
    is_tarfile: bool = False,
):
    if file_bytes is None:
        # Load File ID
        file = fetch_file(file_id)
        file_bytes = BytesIO(file.data.encode("utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        if is_zip:
            staged_path = _stage_files_zip(file_bytes, target_folder, tmpdir)
        elif is_tarfile:
            staged_path = _stage_files_tarfile(file_bytes, target_folder, tmpdir)
        else:
            raise PluginValidationError("Unknown Compression Library")

        staged_path = _validate_extracted_folder(staged_path)

        if migrate_conf:
            _migrate_conf(target_folder, staged_path)

        _clean_existing(target_folder)
        _release_plugin(target_folder, staged_path)


def _stage_files_tarfile(file_bytes: BytesIO, target_folder: str, tmpdir: str) -> Path:

    target_path = Path(f"{tmpdir}/{target_folder}").resolve()
    with tarfile.open(fileobj=file_bytes, mode="r:gz") as tar:
        tar.extractall(path=target_path)

    return target_path


def _stage_files_zip(file_bytes: BytesIO, target_folder: str, tmpdir: str) -> Path:

    target_path = Path(f"{tmpdir}/{target_folder}").resolve()

    with zipfile.ZipFile(file_bytes, "r") as archive:
        safe_members = []

        for member in archive.infolist():
            # Resolve the absolute path where the file would be extracted
            member_path = (target_path / member.filename).resolve()

            # Check if the path escapes the target directory
            # relative_to will raise a ValueError if it's outside the target
            try:
                member_path.relative_to(target_path)
                safe_members.append(member)
            except ValueError:
                print(
                    f"[!] Warning: Blocked dangerous Zip Slip path: {member.filename}"
                )

        # Extract only the validated members
        archive.extractall(path=target_path, members=safe_members)

    return target_path


def _validate_extracted_folder(staged_folder: Path) -> Path:
    # Sometimes when people compress folders, they make it a nested folder
    # This will handle that pathing update

    if (staged_folder / "beer.conf").exists():
        return staged_folder

    for path in staged_folder.iterdir():
        if path.is_dir():
            if (path / "beer.conf").exists():
                return path
    raise PluginValidationError("Unable to find beer.conf")


def _migrate_conf(target_folder: str, staged_folder: Path):
    target_directory = _get_target_folder_path(target_folder)
    source_conf = Path(f"{target_directory}/beer.conf")
    if source_conf.is_file():
        target_conf = staged_folder / "beer.conf"
        target_conf.parent.mkdir(parents=True, exist_ok=True)
        target_conf.write_bytes(source_conf.read_bytes())


def _get_target_folder_path(target_folder: str):
    plugin_dir = config.get("plugin.local.directory")  # TODO: Fix This Pathing
    if target_folder.startswith(plugin_dir) or target_folder.startswith("/"):
        # Target Path was given in full
        return target_folder
    else:
        # Combine config path and target folder
        if plugin_dir.endswith("/"):
            return plugin_dir + target_folder
        else:
            return f"{plugin_dir}/{target_folder}"


def _clean_existing(target_folder: str):
    # Shutdown instances
    if Path(_get_target_folder_path(target_folder)).is_dir():

        if "/" in target_folder:
            instance_path = target_folder.rsplit("/", 1)[-1]
        else:
            instance_path = target_folder

        # Find runner
        runner_id = None
        for runner in runners():
            if runner.path == instance_path:
                # This is the instance to use to trace back system
                runner_id = runner.id
                break

        # Purge system if anything is running associated
        if runner_id is not None:
            system = db.query_unique(
                System,
                instances__match={
                    "metadata__runner_id": runner_id,
                },
            )
            purge_system(system=system)

        # Delete Folder
        shutil.rmtree(_get_target_folder_path(target_folder))


def _release_plugin(target_folder: str, staged_folder: Path):

    # Move Folder
    target_path = Path(_get_target_folder_path(target_folder))
    shutil.move(staged_folder, target_path)

    # Run Rescan on new folder
    rescan(paths=[target_path])
