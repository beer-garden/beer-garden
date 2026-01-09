# Makefile for Beer-garden UI

DOCKER_NAME    = bgio/ui
VERSION       ?= latest
SHORT_VERSION  = $(shell echo $(VERSION) | head -c 1)

.PHONY: clean clean-build clean-test help test deps
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

deps: ## install javascript dependencies
	node --version
	npm install

build-models:
	pip install py

start:
	PORT=3002 npm start

chromium_test:
	docker run \
		--name=chromium \
		--security-opt seccomp=unconfined `#optional` \
		-e PUID=1000 \
		-e PGID=1000 \
		-e TZ=Etc/UTC \
		-e CHROME_CLI=http://localhost:3002/ `#optional` \
		-p 3000:3000 \
		-p 3001:3001 \
		--shm-size="1gb" \
		--restart unless-stopped \
		--network="host" \
		lscr.io/linuxserver/chromium:latest

chromium_clean:
	docker container prune
	docker image prune
	docker volume prune
	docker image rm -f lscr.io/linuxserver/chromium

format:
	npx prettier --write src/

