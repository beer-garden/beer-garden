#!/usr/bin/env python

import argparse
import itertools
import json
import os
import subprocess
import sys

BUILD_IMAGE = "bgio/build"
NODE_IMAGE = "node:10.9"
SUPPORTED_DISTRIBUTIONS = ["centos7"]
SUPPORTED_PYTHONS = ["python2", "python3"]
BUILD_TYPES = ["rpm"]

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.abspath(os.path.join(SCRIPT_PATH, ".."))
RPM_BUILD_SCRIPT = os.path.join("/", "src", "bin", "rpm_build.sh")


def parse_args(cli_args):
    parser = argparse.ArgumentParser(description="Build beer-garden artifacts.")
    parser.add_argument("type", choices=BUILD_TYPES)
    parser.add_argument("--distribution", choices=SUPPORTED_DISTRIBUTIONS)
    parser.add_argument("--python", choices=SUPPORTED_PYTHONS)
    parser.add_argument("--local", action="store_true", default=False)
    parser.add_argument("--docker-envs", type=json.loads, default="{}")
    return parser.parse_args(cli_args)


def build_rpms(cli_dist, cli_python, local, docker_envs):

    if cli_dist:
        if cli_dist not in SUPPORTED_DISTRIBUTIONS:
            print("Invalid distribution (%s) for RPM build" % cli_dist)
            print("Supported distributions are: %s" % SUPPORTED_DISTRIBUTIONS)
            sys.exit(1)

        build_dists = [cli_dist]
    else:
        build_dists = SUPPORTED_DISTRIBUTIONS

    build_python = cli_python or "python3"
    if build_python not in SUPPORTED_PYTHONS:
        print("Invalid python (%s) for RPM build" % cli_python)
        print("Supported distributions are: %s" % SUPPORTED_PYTHONS)
        sys.exit(1)

    # This massages the input env dict into ["-e", "key=value"]
    # It's gross, don't worry about it
    env_vars = list(
        itertools.chain.from_iterable(
            zip(itertools.repeat("-e"), [k + "=" + v for k, v in docker_envs.items()])
        )
    )

    if local:
        js_cmd = (
            ["docker", "run", "--rm", "-v", SRC_PATH + ":/src"]
            + env_vars
            + [NODE_IMAGE, "make", "-C", "/src/brew-view", "package-js"]
        )
        subprocess.call(js_cmd)

    for dist in build_dists:
        tag = dist + "-" + build_python
        cmd = (
            ["docker", "run", "--rm", "-v", SRC_PATH + ":/src"]
            + env_vars
            + [BUILD_IMAGE + ":" + tag, RPM_BUILD_SCRIPT, "-r", dist[-1]]
        )
        if local:
            cmd.append("--local")
        subprocess.call(cmd)


def main():
    args = parse_args(sys.argv[1:])
    if args.type == "rpm":
        build_rpms(args.distribution, args.python, args.local, args.docker_envs)


if __name__ == "__main__":
    main()
