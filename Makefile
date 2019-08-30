# Makefile for bg-utils

PYTHON        = python
MODULE_NAME   = bg_utils
TEST_DIR      = test

.PHONY: clean clean-build clean-docs clean-test clean-python docs help test

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
deps: ## install python dependencies
	pip install -r requirements.txt

deps-python-master: ## install bg dependencies from master
	pip install -e git+https://github.com/beer-garden/brewtils@master#egg=brewtils

deps-python-develop: ## install bg dependencies from develop
	pip install -e git+https://github.com/beer-garden/brewtils@develop#egg=brewtils


# Cleaning
clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-docs: ## remove doc artifacts
	rm -f docs/$(MODULE_NAME).rst
	rm -f docs/modules.rst

clean-python: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-sphinx: ## requires sphinx to be installed
	$(MAKE) -C docs clean

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

clean-all: clean-build clean-docs clean-python clean-sphinx clean-test ## remove everything

clean: clean-build clean-docs clean-python clean-test ## remove everything but sphinx


# Linting
lint: ## check style with flake8
	flake8 $(MODULE_NAME) $(TEST_DIR)
	black --check $(MODULE_NAME) $(PYTHON_TEST_DIR)


# Testing / Coverage
test-python: ## run tests quickly with the default Python
	pytest $(TEST_DIR)

test-tox: ## run tests on every Python version with tox
	tox

test: test-python ## alias of test-python

coverage: ## check code coverage quickly with the default Python
	coverage run --source $(MODULE_NAME) -m pytest
	coverage report -m
	coverage html

coverage-view: coverage ## view coverage report in a browser
	$(BROWSER) htmlcov/index.html


# Documentation
docs: ## generate Sphinx HTML documentation, including API docs
	sphinx-apidoc -f -o docs/ $(MODULE_NAME)
	$(MAKE) -C docs html

docs-view: docs ## view generated documentation in a browser
	$(BROWSER) docs/_build/html/index.html

docs-serve: docs ## generage the docs and watch for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .


# Packaging
package-source: ## builds source package
	$(PYTHON) setup.py sdist

package-wheel: ## builds wheel package
	$(PYTHON) setup.py bdist_wheel

package: clean package-source package-wheel ## builds source and wheel package
	ls -l dist


# Publishing
publish-package-test: package ## upload a package to the testpypi
	twine upload --repository testpypi dist/*

publish-package: package ## upload a package
	twine upload dist/*
