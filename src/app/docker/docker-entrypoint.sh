#!/bin/sh

if [ -f /etc/beer-garden/requirements.txt ]; then
    pip install -r /etc/beer-garden/requirements.txt
fi

exec gosu beergarden beergarden $@
