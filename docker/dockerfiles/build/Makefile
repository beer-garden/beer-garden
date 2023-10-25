SHELL:=/bin/bash

build-all: | build-image-base build-image-python3.8.18 build-image-python3.9.18 build-image-python3.10.13 build-image-python3.11.6 build-image-python3.12.0

build-image-base: 
	echo "Building: centos7-base"; \
	docker build . -t bgio/build:centos7-base -f centos7-base/Dockerfile; \
	docker push bgio/build:centos7-base;
	

build-image-python3.8.18: 
	echo "Building: centos7-python3.8"; \
	docker build . -t bgio/build:centos7-python3.8 -f centos7-python3.8/Dockerfile; \
	docker tag bgio/build:centos7-python3.8 bgio/build:centos7-python3.8.18; \
	docker push bgio/build:centos7-python3.8; \
	docker push bgio/build:centos7-python3.8.18;

build-image-python3.9.18: 
	echo "Building: centos7-python3.9"; \
	docker build . -t bgio/build:centos7-python3.9 -f centos7-python3.9/Dockerfile; \
	docker tag bgio/build:centos7-python3.9 bgio/build:centos7-python3.9.18; \
	docker push bgio/build:centos7-python3.9; \
	docker push bgio/build:centos7-python3.9.18;

build-image-python3.10.13: 
	echo "Building: centos7-python3.10"; \
	docker build . -t bgio/build:centos7-python3.10 -f centos7-python3.10/Dockerfile; \
	docker tag bgio/build:centos7-python3.10 bgio/build:centos7-python3.10.13; \
	docker push bgio/build:centos7-python3.10; \
	#docker push bgio/build:centos7-python3.10.13; 

build-image-python3.11.6: 
	echo "Building: centos7-python3.10"; \
	docker build . -t bgio/build:centos7-python3.11 -f centos7-python3.11/Dockerfile; \
	docker tag bgio/build:centos7-python3.11 bgio/build:centos7-python3.11.6; \
	docker push bgio/build:centos7-python3.11; \
	docker push bgio/build:centos7-python3.11.6;

build-image-python3.12.0: 
	echo "Building: centos7-python3.12"; \
	docker build . -t bgio/build:centos7-python3.12 -f centos7-python3.12/Dockerfile; \
	docker tag bgio/build:centos7-python3.12 bgio/build:centos7-python3.12.0; \
	docker push bgio/build:centos7-python3.12; \
	docker push bgio/build:centos7-python3.12.0;