# Makefile for integration tests

.PHONY: clean clean-build clean-test clean-pyc help test-all
.DEFAULT_GOAL := help

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


help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

deps:
	pip install -r requirements.txt

lint: ## check style with flake8
	flake8

#test-config: ## run configuration integration tests
#	pytest config/
#
#test-lifecycle: ## run lifecycle integration tests
#	pytest lifecycle/

test-gardens: ## run rest integration tests
	pytest gardens/

test-remote-plugins: ## run rest integration tests
	pytest remote_plugins/

test-local-plugins: ## run rest integration tests
	pytest local_plugins/

test-stomp: ## run rest integration tests
	pytest stomp/