SHELL:=/bin/bash

build-all: | build-image-base build-image-python3.8.18 build-image-python3.9.18 build-image-python3.10.13 build-image-python3.11.6 build-image-python3.12.0
	
build-image-python3.8.18: 
	echo "Building: centos7-python3.8"; \
	docker build -f centos7/Dockerfile . \
		--build-arg PYTHON_VERSION=3.8.18 \
		-t bgio/build:centos7-python3.8.18 \
		--build-arg PYTHON_MINOR_VERSION=3.8 \
		-t bgio/build:centos7-python3.8; \
	docker push bgio/build:centos7-python3.8; \
	docker push bgio/build:centos7-python3.8.18;

build-image-python3.9.18: 
	echo "Building: centos7-python3.9"; \
	docker build -f centos7/Dockerfile . \
		--build-arg PYTHON_VERSION=3.9.18 \
		-t bgio/build:centos7-python3.9.18 \
		--build-arg PYTHON_MINOR_VERSION=3.9 \
		-t bgio/build:centos7-python3.9; \
	docker push bgio/build:centos7-python3.9; \
	docker push bgio/build:centos7-python3.9.18;

build-image-python3.10.13: 
	echo "Building: centos7-python3.10"; \
	docker build -f centos7/Dockerfile . \
		--build-arg PYTHON_VERSION=3.10.13 \
		-t bgio/build:centos7-python3.10.13 \
		--build-arg PYTHON_MINOR_VERSION=3.10 \
		-t bgio/build:centos7-python3.10; \
	docker push bgio/build:centos7-python3.10; \
	docker push bgio/build:centos7-python3.10.13; 

build-image-python3.11.6: 
	echo "Building: centos7-python3.11"; \
	docker build -f centos7/Dockerfile . \
		--build-arg PYTHON_VERSION=3.11.6 \
		-t bgio/build:centos7-python3.11.6 \
		--build-arg PYTHON_MINOR_VERSION=3.11 \
		-t bgio/build:centos7-python3.11; \
	docker push bgio/build:centos7-python3.11; \
	docker push bgio/build:centos7-python3.11.6;

build-image-python3.12.7: 
	echo "Building: centos7-python3.12"; \
	docker build -f centos7/Dockerfile . \
		--build-arg PYTHON_VERSION=3.12.7 \
		-t bgio/build:centos7-python3.12.7 \
		--build-arg PYTHON_MINOR_VERSION=3.12 \
		-t bgio/build:centos7-python3.12; \
	docker push bgio/build:centos7-python3.12; \
	docker push bgio/build:centos7-python3.12.7;

build-image-python3.13.0: 
	echo "Building: centos7-python3.13"; \
	docker build -f centos7/Dockerfile . \
		--build-arg PYTHON_VERSION=3.13.0 \
		-t bgio/build:centos7-python3.13.0 \
		--build-arg PYTHON_MINOR_VERSION=3.13 \
		-t bgio/build:centos7-python3.13; \
	docker push bgio/build:centos7-python3.13; \
	docker push bgio/build:centos7-python3.13.0;


