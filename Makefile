# Makefile for brew-view

MODULE_NAME   = brew_view
PYTHON_TEST_DIR = test/unit
JS_DIR = brew_view/static
DOCKER_NAME = bgio/brew-view
VERSION ?= 0.0.0

.PHONY: clean clean-build clean-test clean-pyc help test deps

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
BROWSER := python -c "$$BROWSER_PYSCRIPT"


# Misc
help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

install: clean ## install the package to the active Python's site-packages
	python setup.py install


# Dependencies
deps-python: ## install python dependencies
	pip install -r requirements.txt

deps-js: ## install js dependencies
	$(MAKE) -C $(JS_DIR) deps

deps-all: deps-js deps-python ## install all dependencies

deps: deps-all ## alias of deps-all

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

clean-all-python: clean-build clean-python clean-test ## remove all python

clean-js: ## remove javascript artifacts
	$(MAKE) -C $(JS_DIR) clean

clean-all: clean-all-python clean-js ## remove everything

clean: clean-all ## alias of clean-all


# Linting
lint-python: ## check python style with flake8
	flake8 $(MODULE_NAME) $(PYTHON_TEST_DIR)

lint-js: ## check javascript style with eslint
	$(MAKE) -C $(JS_DIR) lint

lint-all: lint-python lint-js ## lint everything

lint: lint-python ## alias of lint-python


# Testing / Coverage
test-python: ## run tests quickly with the default Python
	pytest $(PYTHON_TEST_DIR)

test-tox: ## run tests on every Python version with tox
	tox

test: test-python ## alias of test-python

coverage: ## check code coverage quickly with the default Python
	coverage run --source $(MODULE_NAME) -m pytest test/unit/
	coverage report -m
	coverage html

coverage-view: coverage ## view coverage report in a browser
	$(BROWSER) htmlcov/index.html


# Packaging
package-python: clean-all-python ## builds source and wheel python package
	python setup.py sdist bdist_wheel
	ls -l dist

package-js: clean-js ## builds javascript package
	$(MAKE) -C $(JS_DIR) package

package: package-js package-python ## build everything


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
