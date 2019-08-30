#!/bin/bash

# This script uses sphinx utilities to generate documenation
# from Python docstrings

BASEDIR=$(dirname $(dirname $0))
make -C "$BASEDIR/docs"
