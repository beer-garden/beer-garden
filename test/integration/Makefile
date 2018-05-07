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
	flake8 $(MODULE_NAME) $(TEST_DIR)

start: ## start brew-view and bartender
	brew-view &
	bartender &

stop: ## kill brew-view and bartender
	pkill bartender
	sleep 3
	pkill brew-view

test-lifecycle: ## run lifecycle integration tests
	pytest lifecycle/

test-rest: ## run rest integration tests
	$(MAKE) start
	sleep 10
	pytest rest/
	$(MAKE) stop

test-all: test-lifecycle test-rest ## run all the tests
