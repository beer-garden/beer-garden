# Makefile for Beer Garden application

PYTHON          = python
MODULE_NAME     = beer_garden
TEST_DIR        = test
DOCKER_NAME     = bgio/beer-garden

MAX_CYCLOMATIC_COMPLEXITY = 10

VERSION        ?= $(shell python -c "import os; import sys; sys.path.insert(1, './beer_garden/'); from __version__ import __version__; print(__version__);")
SHORT_VERSION   = $(shell echo $(VERSION) | head -c 1)

PYTHON_VERSION ?= 3.12

DATE           ?= $(shell date +%Y-%m-%dT%H)

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

install: clean ## install the package to the active Python's site-packages
	$(PYTHON) setup.py install


# Dependencies
deps-python: ## install python dependencies
	pip install -r requirements.txt -r requirements-dev.txt

deps-python-master: ## install bg dependencies from master
	pip install -e git+https://github.com/beer-garden/brewtils@master#egg=brewtils

deps-python-develop: ## install bg dependencies from develop
	pip install -e git+https://github.com/beer-garden/brewtils@develop#egg=brewtils

deps-compile: ## Generate the requirements.txt and requirements-dev.txt files
	pip install pip-tools && pip install --upgrade pip-tools  ## https://github.com/jazzband/pip-tools/issues/1558
	pip-compile
	pip-compile requirements-dev.in

deps-upgrade: ## Generate requirements files, updating all dependencies where possible
	pip install pip-tools
	pip-compile --upgrade
	pip-compile --upgrade requirements-dev.in

deps: deps-python ## alias of deps-python


# Cleaning
clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-python: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

clean-all: clean-build clean-python clean-test ## remove all python

clean: clean-all ## alias of clean-all


# Formatting
format: ## Run black formatter in-line
	black -t py311 -t py312 -t py313 $(MODULE_NAME) $(TEST_DIR)
	isort --thirdparty brewtils $(MODULE_NAME) $(TEST_DIR)
	$(MAKE) lint


# Linting
lint: ## check style with flake8, black and isort
	flake8 --ignore=F824 $(MODULE_NAME) $(TEST_DIR)
	black -t py311 -t py312 -t py313 --check --diff $(MODULE_NAME) $(TEST_DIR)
	isort --check-only --diff --thirdparty brewtils $(MODULE_NAME)	


# Complexity checks
complexity: ## check function complexity
	flake8 --max-complexity $(MAX_CYCLOMATIC_COMPLEXITY) $(MODULE_NAME)

# Security linting
security: ## check code for insecure settings and functions
	bandit -r $(MODULE_NAME)


# Testing / Coverage
test: ## run tests quickly with the default Python
	pytest $(TEST_DIR) --ignore $(TEST_DIR)/api/http/unit/handlers/v1/event_test.py

coverage: ## check code coverage quickly with the default Python
	coverage run --source $(MODULE_NAME) -m pytest $(TEST_DIR) --tb=no --ignore $(TEST_DIR)/api/http/unit/handlers/v1/event_test.py
	coverage report -m
	coverage html

coverage-view: coverage ## view coverage report in a browser
	$(BROWSER) htmlcov/index.html


# Packaging
package-source: ## builds source package
	$(PYTHON) setup.py sdist

package-wheel: ## builds wheel package
	$(PYTHON) setup.py bdist_wheel

package: clean package-source package-wheel ## builds source and wheel package
	ls -l dist

parse_branch_name:
	$(eval BRANCH_NAME := $(shell git rev-parse --abbrev-ref HEAD))

# Docker
docker-build:
	docker build -t $(DOCKER_NAME):$(VERSION)-python$(PYTHON_VERSION) -f docker/Dockerfile --build-arg VERSION=$(VERSION) --build-arg PYTHON_IMAGE=python:$(PYTHON_VERSION)-slim .	
	docker tag $(DOCKER_NAME):$(VERSION)-python$(PYTHON_VERSION) $(DOCKER_NAME):$(SHORT_VERSION)-python$(PYTHON_VERSION)

docker-tag-latest: docker-build
	docker tag $(DOCKER_NAME):$(VERSION)-python$(PYTHON_VERSION) $(DOCKER_NAME):latest
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(VERSION)
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(SHORT_VERSION)

docker-build-unstable: package clean-python
	docker build -t $(DOCKER_NAME):unstable-python$(PYTHON_VERSION) -f docker/Dockerfile.unstable --build-arg PYTHON_IMAGE=python:$(PYTHON_VERSION)-slim .

docker-tag-latest-unstable: docker-build-unstable
	docker tag $(DOCKER_NAME):unstable-python$(PYTHON_VERSION) $(DOCKER_NAME):unstable

publish-docker: docker-build
	docker push $(DOCKER_NAME):$(VERSION)-python$(PYTHON_VERSION)
	docker push $(DOCKER_NAME):$(SHORT_VERSION)-python$(PYTHON_VERSION)

publish-docker-latest: docker-tag-latest publish-docker
	docker push $(DOCKER_NAME):latest
	docker push $(DOCKER_NAME):$(VERSION)
	docker push $(DOCKER_NAME):$(SHORT_VERSION)

publish-docker-unstable: docker-build-unstable ## push the unstable docker image
	docker push $(DOCKER_NAME):unstable-python$(PYTHON_VERSION)

publish-docker-unstable-latest: docker-tag-latest-unstable publish-docker-unstable ## push the unstable docker image
	docker push $(DOCKER_NAME):unstable-python$(PYTHON_VERSION)

publish-branch-docker-unstable: parse_branch_name package clean-python
	docker build -t $(DOCKER_NAME):$(BRANCH_NAME)-$(VERSION)-python$(PYTHON_VERSION) -f docker/Dockerfile.unstable --build-arg PYTHON_IMAGE=python:$(PYTHON_VERSION)-slim .
	docker push $(DOCKER_NAME):$(BRANCH_NAME)-$(VERSION)-python$(PYTHON_VERSION)

# Publishing
publish-package-test: package ## upload a package to the testpypi
	twine upload --repository testpypi dist/*

publish-package: package ## upload a package
	twine upload dist/*

