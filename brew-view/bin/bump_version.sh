#!/bin/bash

# works with a file called _version.py in the top module directory,
# the contents of which should be a semantic version number
# such as '__version__ = "1.2.3"'

# This script will display the current version, automatically
# suggest a "patch" version update, and ask for input to use
# the suggestion, or a newly entered value.

# once the new version number is determined, the script will
# create a GIT tag.

BINDIR=$(dirname $0)
BASEDIR=$(dirname $BINDIR)
MODULE_NAME="brew_view"
VERSION="$BASEDIR/$MODULE_NAME/_version.py"
if [ -f $VERSION ]; then
    BASE_STRING=$(cat $VERSION | cut -d'"' -f2)
    echo "Current Version: $BASE_STRING"

    BASE_LIST=(`echo $BASE_STRING | tr '.' ' '`)
    V_MAJOR=${BASE_LIST[0]}
    V_MINOR=${BASE_LIST[1]}
    V_PATCH=${BASE_LIST[2]}
    V_EXTRA=${BASE_LIST[3]}

    read -p "Are you making a release? [y/N]: " RESPONSE
    if [ "$RESPONSE" = "Y" ]; then RESPONSE="y"; fi
    if [ "$RESPONSE" = "Yes" ]; then RESPONSE="y"; fi
    if [ "$RESPONSE" = "yes" ]; then RESPONSE="y"; fi
    if [ "$RESPONSE" = "YES" ]; then RESPONSE="y"; fi
    if [ "$RESPONSE" = "y" ]; then 
        SUGGESTED_VERSION="$V_MAJOR.$V_MINOR.$V_PATCH"
        read -p "Enter a version number [$SUGGESTED_VERSION]: " INPUT_STRING
    else
        if [ -z $V_EXTRA ]; then
            let "V_MINOR += 1"
            V_DEV="0"
        else
            V_DEV=${V_EXTRA:3}
            let "V_DEV += 1"
        fi
        SUGGESTED_VERSION="$V_MAJOR.$V_MINOR.$V_PATCH.dev$V_DEV"
        read -p "Enter a version number [$SUGGESTED_VERSION]: " INPUT_STRING
    fi

    if [ "$INPUT_STRING" = "" ]; then
        INPUT_STRING=$SUGGESTED_VERSION
    fi
    if [[ ! "$INPUT_STRING" =~ ^[0-9]+\.[0-9]+\.[0-9]+(\.dev[0-9])*$ ]]; then
        echo "Bad Version $INPUT_STRING. Needs to match X.X.X.devX where X is a number."
        exit 1
    fi
    echo "Will set new version to be $INPUT_STRING"
    echo "__version__ = \"$INPUT_STRING\"" > $VERSION

    git add $VERSION
    # There is a jenkins job based on this commit message. Please be sure you update it if you 
    # choose to change the commit message string from something other than "Version bump to"
    git commit -m "Version bump to $INPUT_STRING"
    git push origin
else
    echo "Could not find a version file."
    read -p "Do you want to create a version file and start from scratch? [y]" RESPONSE
    if [ "$RESPONSE" = "" ]; then RESPONSE="y"; fi
    if [ "$RESPONSE" = "Y" ]; then RESPONSE="y"; fi
    if [ "$RESPONSE" = "Yes" ]; then RESPONSE="y"; fi
    if [ "$RESPONSE" = "yes" ]; then RESPONSE="y"; fi
    if [ "$RESPONSE" = "YES" ]; then RESPONSE="y"; fi
    if [ "$RESPONSE" = "y" ]; then 
        echo "__version__ = \"0.0.1\"" > $VERSION
        git add $VERSION
        git commit -m "Added $VERSION file, Version bump to v0.0.1"
        git tag -a -m "Tagging version 0.0.1" "0.0.1"
        git push origin
        git push origin --tags
    fi
fi
