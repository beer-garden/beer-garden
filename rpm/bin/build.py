#!/usr/bin/env python3

import argparse
import glob
import itertools
import json
import os
import subprocess
import sys
import tarfile

BUILD_IMAGE = "bgio/build"
NODE_IMAGE = "node:18"
SUPPORTED_DISTRIBUTIONS = ["centos7"]
SUPPORTED_PYTHONS = ["3.7"]
BUILD_TYPES = ["rpm"]

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.abspath(os.path.join(SCRIPT_PATH, "..", ".."))
RPM_BUILD_SCRIPT = os.path.join("/", "rpm_build.sh")


def parse_args(cli_args):
    parser = argparse.ArgumentParser(description="Build beer-garden artifacts.")
    parser.add_argument("type", choices=BUILD_TYPES)
    parser.add_argument("version")
    parser.add_argument("--iteration", default="1")
    parser.add_argument("--distribution", choices=SUPPORTED_DISTRIBUTIONS)
    parser.add_argument("--python", choices=SUPPORTED_PYTHONS)
    parser.add_argument("--local", action="store_true", default=False)
    parser.add_argument("--docker-envs", type=json.loads, default="{}")
    return parser.parse_args(cli_args)


def find_and_extract_react_ui():
    release_path = f"{BASE_PATH}/src"

    try:
        react_ui_tarball = glob.glob(f"{release_path}/react-ui*.tar.gz")[0]
    except IndexError:
        print("Could not locate react release tarball in ${release_path}")
        sys.exit(1)

    with tarfile.open(react_ui_tarball) as _file:
        _file.extractall(f"{release_path}/")

    os.remove(react_ui_tarball)

    # rename the directory to something consistent
    react_ui_dir = glob.glob(f"{release_path}/*react-ui*")[0]
    os.rename(react_ui_dir, f"{release_path}/react-ui")


def build_rpms(version, iteration, cli_dist, cli_python, local, docker_envs):

    if cli_dist:
        if cli_dist not in SUPPORTED_DISTRIBUTIONS:
            print("Invalid distribution (%s) for RPM build" % cli_dist)
            print("Supported distributions are: %s" % SUPPORTED_DISTRIBUTIONS)
            sys.exit(1)

        build_dists = [cli_dist]
    else:
        build_dists = SUPPORTED_DISTRIBUTIONS

    build_python = cli_python or "3.7"
    if build_python not in SUPPORTED_PYTHONS:
        print("Invalid python (%s) for RPM build" % cli_python)
        print("Supported distributions are: %s" % SUPPORTED_PYTHONS)
        sys.exit(1)

    find_and_extract_react_ui()

    # This massages the input env dict into ["-e", "key=value"]
    # It's gross, don't worry about it
    env_vars = list(
        itertools.chain.from_iterable(
            zip(itertools.repeat("-e"), [k + "=" + v for k, v in docker_envs.items()])
        )
    )

    ui_build_cmd = (
        ["docker", "run", "--rm", "-v", f"{BASE_PATH}/src:/src"]
        + env_vars
        + [NODE_IMAGE, "make", "-C", "/src/ui", "deps", "package"]
    )

    subprocess.run(ui_build_cmd).check_returncode()

    reactui_build_cmd = (
        ["docker", "run", "--rm", "-v", f"{BASE_PATH}/src:/src"]
        + env_vars
        + ["-e", "PUBLIC_URL=/preview"]
        + [NODE_IMAGE, "make", "-C", "/src/react-ui", "deps", "package"]
    )

    subprocess.run(reactui_build_cmd).check_returncode()

    for dist in build_dists:
        tag = f"{dist}-python{build_python}"
        cmd = (
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "host",
                "-v",
                f"{BASE_PATH}/src:/src",
                "-v",
                f"{BASE_PATH}/rpm:/rpm",
                "-v",
                f"{SCRIPT_PATH}/rpm_build.sh:{RPM_BUILD_SCRIPT}",
            ]
            + env_vars
            + [
                BUILD_IMAGE + ":" + tag,
                RPM_BUILD_SCRIPT,
                "-r",
                dist[-1],
                "-v",
                version,
                "-i",
                iteration,
            ]
        )

        if local:
            cmd.append("--local")

        subprocess.run(cmd).check_returncode()


def main():
    args = parse_args(sys.argv[1:])
    if args.type == "rpm":
        build_rpms(
            args.version,
            args.iteration,
            args.distribution,
            args.python,
            args.local,
            args.docker_envs,
        )


if __name__ == "__main__":
    main()
