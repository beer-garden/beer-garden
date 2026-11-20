DOCKER_NAME     = bgio/metrics
VERSION         ?= $(shell python -c "import os; import sys; sys.path.insert(1, './metrics/'); from __version__ import __version__; print(__version__);")
SHORT_VERSION   = $(shell echo $(VERSION) | head -c 1)
DATE            ?= $(shell date +%Y-%m-%d)

# Formatting
format: ## Run black formatter in-line
	black -t py311 -t py312 -t py313 .
	isort --thirdparty brewtils .
	$(MAKE) lint

# Linting
lint: ## check style with flake8, black and isort
	flake8 --ignore=F824,W503 .
	black -t py311 -t py312 -t py313 --check --diff .
	isort --check-only --diff --thirdparty brewtils .

# Docker
docker-build: ## build docker image
	docker build -t $(DOCKER_NAME):latest . --build-arg VERSION=$(VERSION)
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(VERSION)
	docker tag $(DOCKER_NAME):latest $(DOCKER_NAME):$(SHORT_VERSION)

docker-build-unstable: package ## build nightly docker image
	docker build --pull -t $(DOCKER_NAME):unstable . --build-arg VERSION="unstable"

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
