#!/bin/sh

if [ -f /conf/requirements.txt ]; then
    pip install -r /conf/requirements.txt
fi

beergarden $@
