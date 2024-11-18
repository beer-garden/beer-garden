SHELL:=/bin/bash
PYTHON_VERSION       ?= 0.0.0
PYTHON_SHORT_VERSION  = $(shell echo $(VERSION) | cut -f1,2 -d'.')

build-image-centos7: 
	echo "Building: centos7-python$(PYTHON_VERSION)"; \
	docker build -f centos7/Dockerfile . \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		-t bgio/build:centos7-python$(PYTHON_VERSION)\
		--build-arg PYTHON_MINOR_VERSION=$(PYTHON_SHORT_VERSION) \
		-t bgio/build:centos7-python$(PYTHON_SHORT_VERSION); \
	docker push bgio/build:centos7-python$(PYTHON_SHORT_VERSION); \
	docker push bgio/build:centos7-python$(PYTHON_VERSION);


build-image-rocky9: 
	echo "Building: rocky9-python$(PYTHON_VERSION)"; \
	docker build -f rocky9/Dockerfile . \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		-t bgio/build:rocky9-python$(PYTHON_VERSION) \
		--build-arg PYTHON_MINOR_VERSION=$(PYTHON_SHORT_VERSION) \
		-t bgio/build:rocky9-python$(PYTHON_SHORT_VERSION); \
	docker push bgio/build:rocky9-python$(PYTHON_SHORT_VERSION); \
	docker push bgio/build:rocky9-python$(PYTHON_VERSION);

