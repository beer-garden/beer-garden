# Makefile for Beer Garden

PYTHON         = python
MODULE_NAME    = beer_garden
APP_DIR        = src/app
UI_DIR         = src/ui
REACT_DIR      = src/react

VERSION          ?= 0.0.0
PYTHON_VERSION   ?=3.11
DIST             ?=rocky9
DATE             ?= $(shell date +%Y-%m-%dT%H)

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
rpm-build:  ## build rpm
	rpm/bin/build.py rpm $(VERSION) --iteration py$(PYTHON_VERSION) --python $(PYTHON_VERSION) --distribution $(DIST)

rpm-build-local:  ## build local rpm
	rpm/bin/build.py rpm --local $(VERSION) --iteration py$(PYTHON_VERSION) --python $(PYTHON_VERSION) --distribution $(DIST)

# Docker
docker-login: ## log in to the docker registry
	echo "${DOCKER_PASSWORD}" | docker login -u "${DOCKER_USER}" --password-stdin

docker-build: ## build docker images
	$(MAKE) -C $(APP_DIR) docker-build
	$(MAKE) -C $(UI_DIR) docker-build
	$(MAKE) -C $(REACT_DIR) docker-build

docker-build-unstable: ## build unstable docker images
	$(MAKE) -C $(APP_DIR) docker-build-unstable
	$(MAKE) -C $(UI_DIR) docker-build-unstable
	$(MAKE) -C $(REACT_DIR) docker-build-unstable


# GitHub
github-release: ## create a github release
	http --session=github \
	  https://api.github.com/repos/beer-garden/beer-garden/releases \
	  tag_name=$(VERSION) \
	  name=$(VERSION)


# Publishing
publish-docker: ## push the docker image
	$(MAKE) -C $(APP_DIR) publish-docker
	$(MAKE) -C $(UI_DIR) deps publish-docker
	$(MAKE) -C $(REACT_DIR) deps publish-docker

publish-docker-unstable: ## push the unstable docker image
	$(MAKE) -C $(APP_DIR) publish-docker-unstable
	$(MAKE) -C $(UI_DIR) deps publish-docker-unstable
	$(MAKE) -C $(REACT_DIR) deps publish-docker-unstable

publish-rpm: ## publish the rpm
	rpm/bin/upload.sh $(VERSION) py$(PYTHON_VERSION)

# Requires the docker image already built and UI packaged
publish-docker-rpm: rpm-build
	docker build -t bgio/beer-garden:$(VERSION)-RPM-$(PYTHON_VERSION)-${DIST} -f docker/dockerfiles/bundle_rpm/Dockerfile --build-arg VERSION=$(VERSION) --build-arg PYTHON_VERSION=$(PYTHON_VERSION) .
	docker push bgio/beer-garden:$(VERSION)-RPM-$(PYTHON_VERSION)-${DIST}

parse_unstable_version:
	$(eval VERSION := $(shell python -c "import os; import sys; sys.path.insert(1, './src/app/beer_garden/'); from __version__ import __version__; print(__version__);"))

parse_branch_name:
	$(eval BRANCH_NAME := $(shell git rev-parse --abbrev-ref HEAD))

# Requires the docker image already built and UI packaged
publish-docker-unstable-rpm: parse_unstable_version rpm-build-local
	docker build -t bgio/beer-garden:unstable-RPM-$(PYTHON_VERSION)-${DIST} -f docker/dockerfiles/bundle_rpm/Dockerfile --build-arg VERSION=unstable --build-arg PYTHON_VERSION=$(PYTHON_VERSION) .
	docker push bgio/beer-garden:unstable-RPM-$(PYTHON_VERSION)-${DIST}

publish-docker-unstable-branch-rpm: parse_branch_name parse_unstable_version rpm-build-local
	docker build -t bgio/beer-garden:$(BRANCH_NAME)-$(VERSION)-python$(PYTHON_VERSION)-${DIST}-RPM -f docker/dockerfiles/bundle_rpm/Dockerfile --build-arg VERSION=$(BRANCH_NAME)-$(VERSION) --build-arg PYTHON_VERSION=$(PYTHON_VERSION) .
	docker push bgio/beer-garden:$(BRANCH_NAME)-$(VERSION)-python$(PYTHON_VERSION)-${DIST}-RPM

# Setup Environment
setup:
	docker-compose -f docker/docker-compose/docker-compose.yml up -d mongodb rabbitmq activemq
	$(MAKE) -C $(UI_DIR) deps
	$(MAKE) -C $(APP_DIR) deps-python
	git clone https://github.com/beer-garden/example-plugins.git $(APP_DIR)/plugins

