# Makefile for Beer Garden application

PYTHON         = python
MODULE_NAME    = beer_garden
TEST_DIR       = test
DOCKER_NAME    = bgio/beer-garden

MAX_CYCLOMATIC_COMPLEXITY = 10

VERSION       ?= 0.0.0
SHORT_VERSION  = $(shell echo $(VERSION) | head -c 1)

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
	black $(MODULE_NAME) $(TEST_DIR)
	isort $(MODULE_NAME) $(TEST_DIR)


# Linting
lint: ## check style with flake8, black and isort
	flake8 $(MODULE_NAME) $(TEST_DIR)
	black --check --diff $(MODULE_NAME) $(TEST_DIR)
	isort --check-only --diff --thirdparty brewtils $(MODULE_NAME)


# Complexity checks
complexity: ## check function complexity
	flake8 --max-complexity $(MAX_CYCLOMATIC_COMPLEXITY) $(MODULE_NAME)

# Security linting
security: ## check code for insecure settings and functions
	bandit -r $(MODULE_NAME)


# Testing / Coverage
test: ## run tests quickly with the default Python
	pytest $(TEST_DIR)

coverage: ## check code coverage quickly with the default Python
	coverage run --source $(MODULE_NAME) -m pytest $(TEST_DIR) --tb=no 
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


# Docker
docker-build: docker-build-alpine docker-build-debian ## build the docker images

docker-build-alpine:
	docker build -t $(DOCKER_NAME):latest -f docker/Dockerfile.alpine --build-arg VERSION=$(VERSION) .
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(VERSION)
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(VERSION)-python3.11
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(SHORT_VERSION)
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(SHORT_VERSION)-python3.11
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(VERSION)-alpine
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(SHORT_VERSION)-alpine

	docker build -t $(DOCKER_NAME):$(VERSION)-python3.7 -f docker/Dockerfile.alpine --build-arg VERSION=$(VERSION) --build-arg PYTHON_IMAGE=python:3.7-alpine .	
	docker build -t $(DOCKER_NAME):$(VERSION)-python3.8 -f docker/Dockerfile.alpine --build-arg VERSION=$(VERSION) --build-arg PYTHON_IMAGE=python:3.8-alpine .
	docker build -t $(DOCKER_NAME):$(VERSION)-python3.9 -f docker/Dockerfile.alpine --build-arg VERSION=$(VERSION) --build-arg PYTHON_IMAGE=python:3.9-alpine .
	docker build -t $(DOCKER_NAME):$(VERSION)-python3.10 -f docker/Dockerfile.alpine --build-arg VERSION=$(VERSION) --build-arg PYTHON_IMAGE=python:3.10-alpine .

	docker tag $(DOCKER_NAME):$(VERSION)-python3.7 $(DOCKER_NAME):$(SHORT_VERSION)-python3.7
	docker tag $(DOCKER_NAME):$(VERSION)-python3.8 $(DOCKER_NAME):$(SHORT_VERSION)-python3.8
	docker tag $(DOCKER_NAME):$(VERSION)-python3.9 $(DOCKER_NAME):$(SHORT_VERSION)-python3.9
	docker tag $(DOCKER_NAME):$(VERSION)-python3.10 $(DOCKER_NAME):$(SHORT_VERSION)-python3.10
	docker tag $(DOCKER_NAME):$(VERSION)-python3.11 $(DOCKER_NAME):$(SHORT_VERSION)-python3.11


docker-build-debian:
	docker build -t $(DOCKER_NAME):$(VERSION)-debian -f docker/Dockerfile.debian --build-arg VERSION=$(VERSION) .
	docker tag $(DOCKER_NAME):$(VERSION)-debian $(DOCKER_NAME):$(SHORT_VERSION)-debian

docker-build-unstable: package clean-python ## build nightly docker image
	docker build -t $(DOCKER_NAME):unstable -f docker/Dockerfile.unstable .
	docker tag $(DOCKER_NAME):unstable $(DOCKER_NAME):unstable-python3.11
	
	docker build -t $(DOCKER_NAME):unstable-python3.7 -f docker/Dockerfile.unstable --build-arg PYTHON_IMAGE=python:3.7-alpine .
	docker build -t $(DOCKER_NAME):unstable-python3.8 -f docker/Dockerfile.unstable --build-arg PYTHON_IMAGE=python:3.8-alpine .
	docker build -t $(DOCKER_NAME):unstable-python3.9 -f docker/Dockerfile.unstable --build-arg PYTHON_IMAGE=python:3.9-alpine .
	docker build -t $(DOCKER_NAME):unstable-python3.10 -f docker/Dockerfile.unstable --build-arg PYTHON_IMAGE=python:3.10-alpine .

	docker build -t $(DOCKER_NAME):unstable-debian -f docker/Dockerfile.unstable-debian .


# Publishing
publish-package-test: package ## upload a package to the testpypi
	twine upload --repository testpypi dist/*

publish-package: package ## upload a package
	twine upload dist/*

publish-docker: docker-build ## push the docker images
	docker push $(DOCKER_NAME):latest
	docker push $(DOCKER_NAME):$(VERSION)
	docker push $(DOCKER_NAME):$(VERSION)-python3.7
	docker push $(DOCKER_NAME):$(VERSION)-python3.8
	docker push $(DOCKER_NAME):$(VERSION)-python3.9
	docker push $(DOCKER_NAME):$(VERSION)-python3.10
	docker push $(DOCKER_NAME):$(VERSION)-python3.11
	docker push $(DOCKER_NAME):$(SHORT_VERSION)
	docker push $(DOCKER_NAME):$(SHORT_VERSION)-python3.7
	docker push $(DOCKER_NAME):$(SHORT_VERSION)-python3.8
	docker push $(DOCKER_NAME):$(SHORT_VERSION)-python3.9
	docker push $(DOCKER_NAME):$(SHORT_VERSION)-python3.10
	docker push $(DOCKER_NAME):$(SHORT_VERSION)-python3.11
	docker push $(DOCKER_NAME):$(VERSION)-debian
	docker push $(DOCKER_NAME):$(SHORT_VERSION)-debian

publish-docker-unstable: docker-build-unstable ## push the unstable docker image
	docker push $(DOCKER_NAME):unstable
	docker push $(DOCKER_NAME):unstable-python3.7
	docker push $(DOCKER_NAME):unstable-python3.8
	docker push $(DOCKER_NAME):unstable-python3.9
	docker push $(DOCKER_NAME):unstable-python3.10
	docker push $(DOCKER_NAME):unstable-python3.11
	docker push $(DOCKER_NAME):unstable-debian
