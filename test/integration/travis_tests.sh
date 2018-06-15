#!/bin/sh

if [ "$TRAVIS_BRANCH" = "master" ]; then
	make test-config
fi

make test-lifecycle

# Start up things
brew-view &
bartender &
sleep 10

make test-rest

# Stop everything
pkill bartender
sleep 3
pkill brew-view
