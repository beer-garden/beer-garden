#!/bin/bash

set -e

usage() {
  echo "Usage: rpm_build.sh [OPTION]..."
  echo "Build an RPM distribution of beer-garden."
  echo ""
  echo "Arguments are space separated and are as follows:"
  echo "  -l, --local                  Build local version of all applications"
  echo "  -r, --release [RELEASE]      The fedora release to target. Must be 7."
  echo "  -v, --version [VERSION]      Version for the rpm"
  echo "  -i, --iteration [ITERATION]  Iteration for the rpm"
  echo ""
  exit 1
}

LOCAL="false"

# Parse args
while [[ "$#" -gt 0 ]]; do
  key="$1"

  case $key in
    -l|--local)
    LOCAL="true"
    ;;
    -r|--release)
    RELEASE="$2"
    shift
    ;;
    -v|--version)
    VERSION="$2"
    shift
    ;;
    -i|--iteration)
    ITERATION="$2"
    shift
    ;;
    *) echo "Unknown argument: $key"; usage;;
  esac
  shift
done

if [ -z "$RELEASE" ]; then
  echo "RELEASE not specified, using 7"
  RELEASE="7"
elif [[ "$RELEASE" != "7" ]]; then
  echo "Unsupported RELEASE: ${RELEASE}"
  echo "Supported releases are 7"
  exit 1
fi

if [ -z "$VERSION" ]; then
  echo "VERSION not specified"
  exit 1
fi

if [ -z "$ITERATION" ]; then
  echo "ITERATION not specified, using 1"
  ITERATION="1"
fi

# Constants
APP_NAME="beer-garden"
APP_PATH="/opt/$APP_NAME"

BIN_PATH="$APP_PATH/bin"
INCLUDE_PATH="$APP_PATH/include"
LIB_PATH="$APP_PATH/lib"
SHARE_PATH="$APP_PATH/share"
UI_PATH="$APP_PATH/ui"

PYTHON_BIN="$APP_PATH/bin/python"
PIP_BIN="$APP_PATH/bin/pip"

SRC_PATH="/src"

SCRIPT_BASE="/rpm/centos${RELEASE}/scripts"
BEFORE_INSTALL="before_install.sh"
AFTER_INSTALL="after_install.sh"
BEFORE_REMOVE="before_remove.sh"
AFTER_REMOVE="after_remove.sh"

RESOURCE_BASE="/rpm/centos${RELEASE}/resources"

get_version() {
    echo $(cat "$SRC_PATH/$1/$2/__version__.py" | cut -s -d'"' -f2)
}

install_apps() {

    # Fails with the older pip (19.x) that's on the build image
    $PIP_BIN install -U pip

    if [[ "$LOCAL" == "true" ]]; then
        make -C $SRC_PATH/brewtils -e PYTHON=$PYTHON_BIN package-source
        make -C $SRC_PATH/app -e PYTHON=$PYTHON_BIN package-source

        brewtils_version=$(get_version "brewtils" "brewtils")
        app_version=$(get_version "app" "beer_garden")

        $PIP_BIN install \
                "$SRC_PATH/brewtils/dist/brewtils-$brewtils_version.tar.gz" \
                "$SRC_PATH/app/dist/beer-garden-$app_version.tar.gz"
    else
        $PIP_BIN install beer-garden==${VERSION}
    fi

    mkdir -p "$UI_PATH"
    cp -r "$SRC_PATH/ui/dist" "$UI_PATH/dist"

    mkdir -p "$UI_PATH/conf/conf.d"
    cp "$RESOURCE_BASE/nginx/upstream.conf" "$UI_PATH/conf/conf.d/"
    mkdir -p "$UI_PATH/conf/default.d"
    cp "$RESOURCE_BASE/nginx/bg.conf" "$UI_PATH/conf/default.d/"
}

create_rpm() {
    # We use FPM to build the RPM. FPM makes this much easier then everything else.
    # Below is an explanation of each of the flags and what they do:
    # -f                        If the rpm already exists just overwrite it
    # -t rpm                    Output Type, in our case RPM
    # -n $APP_NAME              Name of the RPM
    # -v $VERSION               RPM version
    # -a x86_64                 Specifies the Architecture
    # --rpm-dist "el$RELEASE"   The rpm distribution
    # --iteration $ITERATION    The iteration number
    # -s dir                    Describes that the source we are using is a directory
    # -x ""                     Excludes paths matching the given pattern
    # --directories             Recursively mark a directory as 'owned' by the RPM
    # --before-install path     Sets before-install script to be run when installing the RPM
    # --after-install path      Sets after-install script to be run when installing the RPM
    # --before-remove path      Sets before-remove script to be run when uninstalling the RPM
    # --after-remove path       Sets after-remove script to be run when uninstalling the RPM
    # --description String      Descrpition metadata on RPM
    # --license                 The license name
    # --url                     Project site url
    # -d "$DEPS"                Specify any necessary package dependencies

    echo "Building beer-garden (${VERSION}) RPM Package..."

    # Construct the fpm arguments
    args=(
        -f
        -t rpm
        -n $APP_NAME
        -v $VERSION
        -a x86_64
        --rpm-dist "el${RELEASE}"
        --iteration $ITERATION
        -s dir
        -x "*.bak"
        -x "*.orig"
        -x "*.pyc"
        -x "*.pyo"
        -x "**/__pycache__"
        --directories $BIN_PATH
        --directories $INCLUDE_PATH
        --directories $LIB_PATH
        --directories $SHARE_PATH
        --directories $UI_PATH
        --before-install $SCRIPT_BASE/$BEFORE_INSTALL
        --after-install $SCRIPT_BASE/$AFTER_INSTALL
        --before-remove $SCRIPT_BASE/$BEFORE_REMOVE
        --after-remove $SCRIPT_BASE/$AFTER_REMOVE
        --description "The beer-garden application"
        --license "MIT"
        --url "https://beer-garden.io"
    )

    # Put the service files in the correct location
    service_paths=()

    if [[ "$RELEASE" == "7" ]]; then
        args+=(-d "openssl-libs >= 1:1.0.2a-1")

        cp "$RESOURCE_BASE/service/beer-garden.service" "/lib/systemd/system/"
        service_paths+=("/lib/systemd/system/beer-garden.service")
    fi

    # Make sure we have a place to put the rpm
    mkdir -p /rpm/dist
    cd /rpm/dist

    # Build it!
    fpm "${args[@]}" "$APP_PATH" "${service_paths[@]}"
}

install_apps
create_rpm

