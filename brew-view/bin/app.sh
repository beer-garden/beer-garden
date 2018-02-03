#!/bin/sh
# This script will start both the Python REST server and a webpack watch to rebuild the bundled javascript when it changes.
# It won't autorefresh your browser. If you're going to be doing a lot of javascript development it's recommended you run the webpack-dev-server. See beergarden.gov for instructions.

APP_ROOT=$(realpath $(dirname $0)/..)

python -m brew_view -c $APP_ROOT/dev_conf/config.json &
P1=$!

npm run watch --prefix $APP_ROOT/brew_view/static &
P2=$!

wait $P1 $P2
