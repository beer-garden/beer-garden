#!/bin/bash

SRC_PATH=$(realpath $(dirname $0)/..)
DOCKER_TAG=${1:-latest}

# Source .build_properties to get some variables
source $SRC_PATH/.build_properties

# The _version.py file is expected to be in the root package and should look like:
# __version__ = "X.X.X"
VERSION=$(cat "$SRC_PATH/$MODULE_NAME/_version.py" | cut -d'"' -f2)

# Don't need a context for this build...
docker build --no-cache -t beer-garden/$PACKAGE_NAME:$DOCKER_TAG --build-arg VERSION=$VERSION - < $SRC_PATH/Dockerfile

