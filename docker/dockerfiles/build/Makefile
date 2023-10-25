SHELL:=/bin/bash

build-all: | install-remote-images build-image-base build-image-python3.8 build-image-python3.9

install-remote-images:
	docker pull --all-tags bgio/build;

build-image-base: 
	@if ["$(docker images -q bgio/build:centos7-base 2> /dev/null)" == ""]; then \
  		echo "Building: centos7-base"; \
		docker build . -t bgio/build:centos7-base -f centos7-base/Dockerfile; \
		docker push bgio/build:centos7-base; \
	fi 

build-image-python3.8.18: 
	@if ["$(docker images -q bgio/build:centos7-python3.8.18 2> /dev/null)" == ""]; then \
  		echo "Building: centos7-python3.8"; \
		docker build . -t bgio/build:centos7-python3.8 -f centos7-python3.8/Dockerfile; \
		docker tag bgio/build:centos7-python3.8 bgio/build:centos7-python3.8.18; \
		docker push bgio/build:centos7-python3.8; \
		docker push bgio/build:centos7-python3.8.18; \
	fi 

build-image-python3.9.18: 
	@if ["$(docker images -q bgio/build:centos7-python3.9.18 2> /dev/null)" == ""]; then \
  		echo "Building: centos7-python3.9"; \
		docker build . -t bgio/build:centos7-python3.9 -f centos7-python3.9/Dockerfile; \
		docker tag bgio/build:centos7-python3.9 bgio/build:centos7-python3.9.18; \
		docker push bgio/build:centos7-python3.9; \
		docker push bgio/build:centos7-python3.9.18; \
	fi 

build-image-python3.10.13: 
	@if ["$(docker images -q bgio/build:centos7-python3.10.13 2> /dev/null)" == ""]; then \
  		echo "Building: centos7-python3.10"; \
		docker build . -t bgio/build:centos7-python3.10 -f centos7-python3.10/Dockerfile; \
		docker tag bgio/build:centos7-python3.10 bgio/build:centos7-python3.10.13; \
		docker push bgio/build:centos7-python3.10; \
		docker push bgio/build:centos7-python3.10.13; \
	fi 

build-image-python3.11.6: 
	@if ["$(docker images -q bgio/build:centos7-python3.11.6 2> /dev/null)" == ""]; then \
  		echo "Building: centos7-python3.10"; \
		docker build . -t bgio/build:centos7-python3.11 -f centos7-python3.11/Dockerfile; \
		docker tag bgio/build:centos7-python3.11 bgio/build:centos7-python3.11.6; \
		docker push bgio/build:centos7-python3.11; \
		docker push bgio/build:centos7-python3.11.6; \
	fi 

build-image-python3.12.0: 
	@if ["$(docker images -q bgio/build:centos7-python3.12.0 2> /dev/null)" == ""]; then \
  		echo "Building: centos7-python3.12"; \
		docker build . -t bgio/build:centos7-python3.12 -f centos7-python3.12/Dockerfile; \
		docker tag bgio/build:centos7-python3.12 bgio/build:centos7-python3.12.0; \
		docker push bgio/build:centos7-python3.12; \
		docker push bgio/build:centos7-python3.12.0; \
	fi 