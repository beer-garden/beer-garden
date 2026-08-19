# Makefile for Beer-garden UI

DOCKER_NAME    = bgio/ui-react
VERSION       ?= latest
SHORT_VERSION  = $(shell echo $(VERSION) | head -c 1)
DATE          ?= $(shell date +%Y-%m-%d)

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

start: deps
	npm start

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
	npx eslint src/ --fix

lint:
	npx eslint src/ 

test_docker_image:
	docker build -f Dockerfile.vitest -t test_server .

package: deps
	rm -rf build
	npm run build
	chmod -R 755 build/

TEST_FILE ?= 
test: test_docker_image
	docker run --rm test_server npx vitest $(TEST_FILE)

# Docker
docker-build: package ## build docker image
	docker build -t $(DOCKER_NAME):latest .
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(VERSION)
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(SHORT_VERSION)

docker-build-unstable: package ## build nightly docker image
	docker build -t $(DOCKER_NAME):unstable .

# Publishing
publish-docker: docker-build ## push the docker image
	docker push $(DOCKER_NAME):latest
	docker push $(DOCKER_NAME):$(VERSION)
	docker push $(DOCKER_NAME):$(SHORT_VERSION)

publish-docker-unstable: docker-build-unstable ## push the unstable docker image
	docker push $(DOCKER_NAME):unstable

publish-branch-docker-unstable: package
	docker build -t $(DOCKER_NAME):branch-unstable-${DATE} .
	docker push $(DOCKER_NAME):branch-unstable-${DATE}

build_preview: deps
	npm run build -- --mode preview

