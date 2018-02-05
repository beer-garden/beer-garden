#!/usr/bin/env sh

mkdir -p output/python

nosetests --with-xcoverage --cover-package=brew_view --cover-tests --cover-erase \
    --xcoverage-file=output/python/cobertura.xml \
    --with-xunit --xunit-file=output/python/test-report.xml \
    --cover-html --cover-html-dir=output/python/html \
    --rednose tests/python/unit

