#!/bin/bash

usage() {
  echo "Usage: rpm_build.sh [OPTION]..."
  echo "Build an RPM distribution of beer-garden."
  echo ""
  echo "Arguments are space separated and are as follows:"
  echo "  -l, --local              Build local version of all applications"
  echo "  -r, --release [RELEASE]  The fedora release to target"
  echo ""
  echo "RELEASE includes supported releases 6,7 for the fedora architecture."
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
    *) echo "Unknown argument: $key"; usage;;
  esac
  shift
done

if [ -z "$RELEASE" ]; then
  echo "RELEASE must be specified."
  usage
elif [[ "$RELEASE" != "7" ]] && [[ "$RELEASE" != "6" ]]; then
  echo "Unsupported RELEASE: ${RELEASE}"
  echo "Supported releases are 7,6"
  exit 1
fi

# Constants
APP_NAME="beer-garden"
APP_PATH="/opt/$APP_NAME"
PYTHON_BIN="$APP_PATH/bin/python"
PIP_BIN="$APP_PATH/bin/pip"
SRC_PATH="/src"
SRC_SCRIPT_PATH="$SRC_PATH/resources/centos${RELEASE}"
BEFORE_INSTALL="before_install.sh"
AFTER_INSTALL="after_install.sh"
BEFORE_REMOVE="before_remove.sh"
AFTER_REMOVE="after_remove.sh"

get_version() {
    echo $(cat "$SRC_PATH/$1/$2/_version.py" | cut -s -d'"' -f2)
}

install_apps() {
    bartender_package="bartender"
    brew_view_package="brew-view"

    if [[ "$LOCAL" == "true" ]]; then
        brewtils_package="brewtils"
        bg_utils_package="bg-utils"

        brewtils_module="brewtils"
        bg_utils_module="bg_utils"
        bartender_module="bartender"
        brew_view_module="brew_view"

        brewtils_version=$(get_version $brewtils_package $brewtils_module)
        bg_utils_version=$(get_version $bg_utils_package $bg_utils_module)
        bartender_version=$(get_version $bartender_package $bartender_module)
        brew_view_version=$(get_version $brew_view_package $brew_view_module)

        build_sdist $SRC_PATH/$brewtils_package
        build_sdist $SRC_PATH/$bg_utils_package
        build_sdist $SRC_PATH/$bartender_package
        build_sdist $SRC_PATH/$brew_view_package

        #$APP_PATH/bin/pip install \
        $PIP_BIN install \
                "$SRC_PATH/$brewtils_package/dist/$brewtils_package-$brewtils_version.tar.gz" \
                "$SRC_PATH/$bg_utils_package/dist/$bg_utils_package-$bg_utils_version.tar.gz" \
                "$SRC_PATH/$bartender_package/dist/$bartender_package-$bartender_version.tar.gz" \
                "$SRC_PATH/$brew_view_package/dist/$brew_view_package-$brew_view_version.tar.gz"
    else
        # If this isn't a local install we don't have versions
        $PIP_BIN install --upgrade -q $bartender_package $brew_view_package
    fi
}

build_sdist() {
    package_path=$1

    pushd $package_path

    ## TODO: Should we use wheels? (package-wheel)
    make -e PYTHON=$PYTHON_BIN clean package-source

    popd
}

create_rpm() {
    # We use FPM to build the RPM. FPM makes this much easier then everything else.
    # Below is an explanation of each of the flags and what they do:
    # -f                        If the rpm already exists in $SRC_PATH/dist just overwrite it
    # -t rpm                    Output Type, in our case RPM
    # -n $APP_NAME              Name of the RPM
    # -v $VERSION               RPM version
    # -a x86_64                 Specifies the Architecture
    # --rpm-dist "el$RELEASE"   The rpm distribution
    # --iteration 1             The iteration number
    # -s dir                    Describes that the source we are using is a directory
    # -x "*.bak"                Excludes any .bak files
    # -x "*.orig"               Excludes and .orig files
    # --before-install path     Sets before-install script to be run when installing the RPM
    # --after-install path      Sets after-install script to be run when installing the RPM
    # --before-remove path      Sets before-remove script to be run when uninstalling the RPM
    # --after-remove path       Sets after-remove script to be run when uninstalling the RPM
    # --description String      Descrpition metadata on RPM
    # --license                 The license name
    # --url                     Project site url
    # -d "$DEPS"                Specify any necessary package dependencies
    mkdir -p $SRC_PATH/dist
    VERSION=$(cat $SRC_PATH/resources/version)
    echo "Building beer-garden (${VERSION}) RPM Package..."
    cd $SRC_PATH/dist

    args=(
        -f
        -t rpm
        -n $APP_NAME
        -v $VERSION
        -a x86_64
        --rpm-dist "el${RELEASE}"
        --iteration 1
        -s dir
        -x "*.bak"
        -x "*.orig"
        --before-install $SRC_SCRIPT_PATH/$BEFORE_INSTALL
        --after-install $SRC_SCRIPT_PATH/$AFTER_INSTALL
        --before-remove $SRC_SCRIPT_PATH/$BEFORE_REMOVE
        --after-remove $SRC_SCRIPT_PATH/$AFTER_REMOVE
        --description "The beer-garden application"
        --license "MIT"
        --url "https://beer-garden.io"
    )

    if [[ "$RELEASE" == "7" ]]; then
        args+=(-d "openssl-libs >= 1:1.0.2a-1")
    fi

    fpm "${args[@]}" $APP_PATH
}

install_apps
create_rpm

