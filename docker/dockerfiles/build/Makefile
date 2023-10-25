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

build-image-python3.8: 
	@if ["$(docker images -q bgio/build:centos7-python3.8 2> /dev/null)" == ""]; then \
  		echo "Building: centos7-python3.8"; \
		docker build . -t bgio/build:centos7-python3.8 -f centos7-python3.8/Dockerfile; \
		docker push bgio/build:centos7-python3.8; \
	fi 

build-image-python3.9: 
	@if ["$(docker images -q bgio/build:centos7-python3.9 2> /dev/null)" == ""]; then \
  		echo "Building: centos7-python3.9"; \
		docker build . -t bgio/build:centos7-python3.9 -f centos7-python3.9/Dockerfile; \
		docker push bgio/build:centos7-python3.9; \
	fi 