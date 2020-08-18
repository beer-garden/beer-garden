# Makefile for Beer Garden

PYTHON         = python
MODULE_NAME    = beer_garden
APP_DIR        = src/app
UI_DIR         = src/ui
DOCKER_NAME    = bgio/beer-garden
DOCKERFILE_DIR = docker/dockerfiles

VERSION        ?= 0.0.0

.PHONY: clean clean-build clean-test clean-pyc help test

.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT
BROWSER := $(PYTHON) -c "$$BROWSER_PYSCRIPT"


# Misc
help:
	@$(PYTHON) -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)


# RPM
rpm-build-local:  # build the rpm
	$(PYTHON) rpm/bin/build.py rpm --local $(VERSION)


# Docker
docker-login: ## log in to the docker registry
	echo "${DOCKER_PASSWORD}" | docker login -u "${DOCKER_USER}" --password-stdin

docker-build-unstable: ## build unstable docker images
	$(MAKE) -C $(APP_DIR) docker-build-unstable
	$(MAKE) -C $(UI_DIR) docker-build-unstable


# Publishing
publish-docker-unstable: ## push the unstable docker image
	$(MAKE) -C $(APP_DIR) publish-docker-unstable
	$(MAKE) -C $(UI_DIR) deps publish-docker-unstable
