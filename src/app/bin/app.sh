#!/bin/bash

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_ROOT="$(dirname "$SCRIPT_DIRECTORY")"

CONFIG_FILE="$APP_ROOT/example_configs/config.yaml"
LOG_CONFIG_FILE="$APP_ROOT/example_configs/logging-config.yaml"

CMD="beer_garden -c $CONFIG_FILE -l $LOG_CONFIG_FILE"
python -m $CMD
