# Centos 7 Build Image
#
# This image is for building a Rocky 9 compatible RPM for beer-garden
#
# It comes with:
#
#  * Python installed
#  * FPM installed for package management
#  * Build essential stuff

FROM rockylinux:9.3

ARG PYTHON_VERSION
ARG PYTHON_MINOR_VERSION

ENV LANG=en_US.UTF-8 \
    APP_HOME=/opt/beer-garden

USER root

RUN yum install -y \
        gcc \
        gcc-c++ \
        zlib \
        zlib-devel \
        curl-devel \
        libffi-devel \
        readline-devel \
        rpm-build \
        tar \
        make \
        bzip2-devel \
        sqlite-devel \
        perl-core \
        pcre-devel \
        wget \
        zlib-devel


# Install GEM Packages
RUN yum install -y rubygems
RUN gem install fpm

# Install Python
RUN mkdir -p /usr/src/python && \
    mkdir -p $APP_HOME  && \
    curl https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz -o Python-${PYTHON_VERSION}.tar.xz && \
    tar -xC /usr/src/python/ --strip-components=1 -f Python-${PYTHON_VERSION}.tar.xz && \
    rm -f Python-${PYTHON_VERSION}.tar.xz
RUN cd /usr/src/python && \
    ./configure --prefix=$APP_HOME && \
    make altinstall prefix=$APP_HOME exec-prefix=$APP_HOME && \
    $APP_HOME/bin/python${PYTHON_MINOR_VERSION} -m "ensurepip"
RUN cd $APP_HOME/bin && \
    ln -fs python${PYTHON_MINOR_VERSION} python && ln -fs pip${PYTHON_MINOR_VERSION} pip && \
    find $APP_HOME -type d '(' -name '__pycache__' -o -name 'test' -o -name 'tests' ')' -exec rm -rfv '{}' + && \
    find $APP_HOME -type f '(' -name '*.py[co]' -o -name '*.exe' ')' -exec rm -fv '{}' +  && \
    rm -rf /usr/src/python
