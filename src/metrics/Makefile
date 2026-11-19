DOCKER_NAME     = bgio/beer-garden
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
	flake8 --ignore=F824 .
	black -t py311 -t py312 -t py313 --check --diff .
	isort --check-only --diff --thirdparty brewtils .

# Docker
docker-build: package ## build docker image
	docker build --pull -t $(DOCKER_NAME):latest-metrics . --build-arg VERSION=$(VERSION)
	docker tag $(DOCKER_NAME):latest-metrics $(DOCKER_NAME):$(VERSION)-metrics
	docker tag $(DOCKER_NAME):latest-metrics $(DOCKER_NAME):$(SHORT_VERSION)-metrics

docker-build-unstable: package ## build nightly docker image
	docker build --pull -t $(DOCKER_NAME):unstable-metrics . --build-arg VERSION="unstable"

# Publishing
publish-docker: docker-build ## push the docker image
	docker push $(DOCKER_NAME):latest-metrics
	docker push $(DOCKER_NAME):$(VERSION)-metrics
	docker push $(DOCKER_NAME):$(SHORT_VERSION)-metrics

publish-docker-unstable: docker-build-unstable ## push the unstable docker image
	docker push $(DOCKER_NAME):unstable-metrics

publish-branch-docker-unstable: package
	docker build -t $(DOCKER_NAME):branch-unstable-metrics-${DATE} .
	docker push $(DOCKER_NAME):branch-unstable-metrics-${DATE}
