#!/usr/bin/env python

import argparse
import sys
import subprocess
import os

BUILD_IMAGE = "beer-garden/build"
CENTOS6 = 'centos6'
CENTOS7 = 'centos7'
PYTHON_VERSION = "python2"
FEDORA_DISTRIBUTIONS = [CENTOS6, CENTOS7]
SUPPORTED_DISTRIBUTIONS = FEDORA_DISTRIBUTIONS
BUILD_TYPES = ['rpm']

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.abspath(os.path.join(SCRIPT_PATH, '..'))
RPM_BUILD_SCRIPT = os.path.join("/", "src", "bin", "build_rpm.sh")


def parse_args(cli_args):
    parser = argparse.ArgumentParser(description="Build beer-garden artifacts.")
    parser.add_argument('type', choices=BUILD_TYPES)
    parser.add_argument('--distribution', choices=SUPPORTED_DISTRIBUTIONS, default='rhel7')
    parser.add_argument('--local', action='store_true', default=False)
    return parser.parse_args(cli_args)


def build_rpm(dist, local):
    if dist not in FEDORA_DISTRIBUTIONS:
        print("Invalid distribution (%s) for RPM build" % dist)
        print("Supported distributions are: %s" % FEDORA_DISTRIBUTIONS)
        sys.exit(1)

    cmd = ["docker", "run", "-v", SRC_PATH + ":/src", "--rm"]

    if dist == CENTOS6:
        cmd += [BUILD_IMAGE + ":centos6-" + PYTHON_VERSION, RPM_BUILD_SCRIPT, "-r", "6"]
    elif dist == CENTOS7:
        cmd += [BUILD_IMAGE + ":centos7-" + PYTHON_VERSION, RPM_BUILD_SCRIPT, "-r", "7"]
    else:
        print("No build image could be determined for %s" % dist)
        sys.exit(1)

    if local:
        cmd += ["--local"]

    subprocess.call(cmd)


def main():
    args = parse_args(sys.argv[1:])
    if args.type == 'rpm':
        build_rpm(args.distribution, args.local)
    else:
        print("Unsupported build type %s" % args.type)
        sys.exit(1)


if __name__ == "__main__":
    main()
