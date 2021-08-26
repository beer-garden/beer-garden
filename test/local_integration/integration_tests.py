#!/usr/bin/env python3
"""Run BeerGarden integration tests locally."""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import docker
import pytest
from docker import DockerClient
from docker.errors import APIError, BuildError, DockerException
from docker.models.containers import Container
from docker.models.images import Image
from docker.models.volumes import VolumeCollection
from testcontainers.compose import DockerCompose

ENV_FILENAME = "integration_env"
BG_CONTAINER_NAME = "integration_local_beer-garden_1"
BG_CHILD_CONTAINER_NAME = "integration_local_beer-garden_1"
CONTAINERS = {
    "beer garden": "integration_local_beer-garden_1",
    "beer garden child": "integration_local_beer-garden-child_1",
    "activemq": "integration_local_activemq_1",
    "mongodb": "integration_local_mongodb_1",
    "rabbitmq": "integration_local_rabbitmq_1",
}
BG_IMAGE_NAME = "beer_garden_integration_tests"
BG_IMAGE_TAGS = BG_IMAGE_NAME + ":latest"
ALL_IMAGES = ["mongodb", "rabbitmq", "beer-garden", "beer-garden-child"]
VOLUMES = {
    "integration_local_mongo-config",
    "integration_local_mongo-data",
    "integration_local_rabbitmq-home",
}
ALL_TESTS = "all"
TEST_SUITE_OPTIONS_BASE = [ALL_TESTS]
OS_ENVIRON_DICT = {"BG_HOST": "localhost", "BG_SSL_ENABLED": str(False)}


def _start_network(
    docker_client: DockerClient, docker_compose_client: DockerCompose
) -> None:
    docker_compose_client.stop()

    if not _remove_volumes(docker_client):
        raise RuntimeError("Unable to remove volumes from previous run")

    docker_compose_client.start()

    for label, container_name in CONTAINERS.items():
        container: Container = docker_client.containers.get(container_name)

        assert (
            container.status == "running"
        ), f"{label} not running after docker-compose ... up, cannot continue"


def _stop_network(
    docker_client: DockerClient, docker_compose_client: DockerCompose
) -> None:
    print("Tearing down beer garden docker images. Please wait...")
    docker_compose_client.stop()

    if not _remove_volumes(docker_client):
        raise ValueError("Unable to remove volumes from this run")


def _remove_volumes(client: DockerClient) -> bool:
    """Remove our important volumes if they are active."""
    volumes: VolumeCollection = client.volumes

    for volume in volumes.list():
        if volume.name in VOLUMES:
            try:
                volume.remove(force=True)
            except DockerException:
                return False

    # also remove volumes that are not in use; this picks up the ones that we add
    # dynamically with docker-compose, but doesn't touch any used by other docker images
    # that might be running
    try:
        volumes.prune()
    except DockerException:
        return False

    return True


def _get_composer(environment: Dict[str, Any], env_file: Path) -> DockerCompose:
    """Create a DockerCompose object with the required .env file."""
    env_file_path = str(env_file)

    if env_file.exists():
        env_file.unlink()
    env_file.touch()

    with env_file.open(mode="w") as file:
        for key, val in environment.items():
            file.write(f"{key}={val}\n")

    return DockerCompose(
        ".",
        compose_file_name="docker-compose-local-integration-tests.yml",
        env_file=env_file_path,
    )


def main(bgarden: Path, btils: Path, tests: List[Path]) -> None:
    """Execute the main logic of the script.

    Args:
        bgarden: Path to the beergarden sources
        btils: Path to the brewtils sources
        tests: List of integration tests to run.
    """
    this_cwd = Path.cwd()
    docker_client: DockerClient = docker.from_env()

    # check if the beer garden container exists and build it if not
    image_collection = docker_client.images

    if not any(BG_IMAGE_TAGS in image.tags for image in image_collection.list()):
        print("Building beer garden docker image. Please wait...")
        new_image: Image
        try:
            new_image, _ = image_collection.build(
                path=str(this_cwd), tag=BG_IMAGE_NAME, rm=True
            )
        except (BuildError, APIError) as exc:
            raise RuntimeError("Unable to build beer garden docker image") from exc

        assert BG_IMAGE_TAGS in new_image.tags

    # create the environment file that docker-compose needs to mount in the needed
    # volumes, namely 1. where on the filesystem the beer-garden source lives
    # and 2. where on the filesystem the brewtils source lives; we also pass which
    # config files to use, since they are different for parent and child
    parent_config = this_cwd / "configs/config.yaml"
    child_config = this_cwd / "configs/config-child.yaml"

    assert (
        parent_config.exists() and child_config.exists()
    ), "Cannot stat config files on host system"

    bg_environment = {
        "APP_SRC": bgarden,
        "BREWTILS_SRC": btils,
        "PARENT_CONFIG": str(parent_config),
        "CHILD_CONFIG": str(child_config),
    }

    # bring up all images
    env_file = this_cwd / ENV_FILENAME
    docker_compose_client = _get_composer(bg_environment, env_file)

    # poke environment variables needed for the integration tests into the local
    # environment
    os.environ.update(OS_ENVIRON_DICT)

    # run the tests
    for test_directory in tests:
        _start_network(docker_client, docker_compose_client)
        pytest.main([str(test_directory)])
        _stop_network(docker_client, docker_compose_client)

    # final tear down
    if env_file.exists():
        env_file.unlink()


if __name__ == "__main__":
    cwd = Path.cwd()
    tests_home = cwd.parent / "integration"
    bad_dirs = {"configs", "helper", "old_v2_stuff"}
    test_dirs_dict = {
        str(x.stem): x
        for x in tests_home.glob("*")
        if x.is_dir() and x.stem not in bad_dirs
    }
    all_tests = list(test_dirs_dict.keys())
    allowed_test_args = TEST_SUITE_OPTIONS_BASE + all_tests

    parser = argparse.ArgumentParser(
        prog="integration_tests",
        description="Run BeerGarden integration tests locally.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "beergarden",
        type=str,
        metavar="beer_garden_path",
        help="The path to the top-level directory of the beer garden sources",
    )
    parser.add_argument(
        "brewtils",
        type=str,
        metavar="brewtils_path",
        help="The path to the top-level directory of the brewtils sources",
    )
    parser.add_argument(
        "--test",
        type=str,
        nargs="*",
        choices=allowed_test_args,
        help="Test suites to run",
        default=TEST_SUITE_OPTIONS_BASE[0],
    )
    args = parser.parse_args()

    bg_path, btils_path = Path(args.beergarden), Path(args.brewtils)

    for name, path in [("beer garden", bg_path), ("brewtils", btils_path)]:
        if not path.exists() or not path.is_dir():
            print(
                f"Argument must point to the top-level directory of the {name} "
                f"sources: {str(bg_path)}"
            )
            sys.exit()

    if args.test is None or len(args.test) == 0 or ALL_TESTS in args.test:
        test_list = list(test_dirs_dict.values())
    else:
        test_list = [test_dirs_dict[test] for test in args.test]

    main(bg_path, btils_path, test_list)
