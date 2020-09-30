#!/bin/bash

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIRECTORY")"
CONFIG_FILE="$APP_ROOT/example_configs/config.yaml"

python -m beer_garden -c "$CONFIG_FILE"
