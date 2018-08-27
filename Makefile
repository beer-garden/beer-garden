# Makefile for bartender

PYTHON        = python
MODULE_NAME   = bartender
TEST_DIR      = test
DOCKER_NAME   = bgio/bartender
VERSION      ?= 0.0.0

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
	pip install -r requirements.txt

deps-python-master: ## install bg dependencies from master
	pip install -e git+https://github.com/beer-garden/bg-utils@master#egg=bg-utils
	pip install -e git+https://github.com/beer-garden/brewtils@master#egg=brewtils

deps-python-develop: ## install bg dependencies from develop
	pip install -e git+https://github.com/beer-garden/bg-utils@develop#egg=bg-utils
	pip install -e git+https://github.com/beer-garden/brewtils@develop#egg=brewtils

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


# Linting
lint: ## check style with flake8
	flake8 $(MODULE_NAME) $(TEST_DIR)


# Testing / Coverage
test: ## run tests quickly with the default Python
	pytest $(TEST_DIR)

test-tox: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source $(MODULE_NAME) -m pytest $(TEST_DIR)
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
docker-build: ## build the docker images
	docker build -t $(DOCKER_NAME):latest --build-arg VERSION=$(VERSION) -f Dockerfile .
	docker build -t $(DOCKER_NAME):latest-python2 --build-arg VERSION=$(VERSION) -f Dockerfile.2 .
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(VERSION)
	docker tag $(DOCKER_NAME):latest-python2 $(DOCKER_NAME):$(VERSION)-python2

docker-build-unstable: package clean-python ## build nightly docker image
	docker build -t $(DOCKER_NAME):unstable -f Dockerfile.unstable .


# Publishing
publish-package-test: package ## upload a package to the testpypi
	twine upload --repository testpypi dist/*

publish-package: package ## upload a package
	twine upload dist/*

publish-docker: docker-build ## push the docker images
	docker push $(DOCKER_NAME):latest
	docker push $(DOCKER_NAME):latest-python2
	docker push $(DOCKER_NAME):$(VERSION)
	docker push $(DOCKER_NAME):$(VERSION)-python2
