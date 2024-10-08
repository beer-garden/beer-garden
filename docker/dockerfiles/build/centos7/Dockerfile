# Centos 7 Build Image
#
# This image is for building a CentOS-7/RHEL-7 compatible RPM for beer-garden
#
# It comes with:
#
#  * Python installed
#  * FPM installed for package management
#  * Build essential stuff

FROM centos/ruby-27-centos7:2.7

ARG PYTHON_VERSION
ARG PYTHON_MINOR_VERSION

ENV LANG=en_US.UTF-8 \
    APP_HOME=/opt/beer-garden

USER root

RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

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

# Install Openssl 1.1.1
RUN wget --no-check-certificate https://ftp.openssl.org/source/openssl-1.1.1k.tar.gz && \
    tar -xzvf openssl-1.1.1k.tar.gz && \
    cd openssl-1.1.1k && \
    ./config --prefix=/usr/local/openssl --openssldir=/usr/local/openssl && \
    make -j $(nproc) && \
    make install && \
    ldconfig && \
    export PATH=/usr/local/openssl/bin:\$PATH && \
    export LD_LIBRARY_PATH=/usr/local/openssl/lib:\$LD_LIBRARY_PATH

# Install GEM Packages
RUN gem install fpm

# Install Python
RUN mkdir -p /usr/src/python && \
    mkdir -p $APP_HOME  && \
    curl https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz -o Python-${PYTHON_VERSION}.tar.xz && \
    tar -xC /usr/src/python/ --strip-components=1 -f Python-${PYTHON_VERSION}.tar.xz && \
    rm -f Python-${PYTHON_VERSION}.tar.xz  && \
    cd /usr/src/python && \
    ./configure --prefix=$APP_HOME --with-openssl=/usr/local/openssl --with-openssl-rpath=auto && \
    make altinstall prefix=$APP_HOME exec-prefix=$APP_HOME && \
    $APP_HOME/bin/python${PYTHON_MINOR_VERSION} -m "ensurepip" && \
    cd $APP_HOME/bin && \
    ln -fs python${PYTHON_MINOR_VERSION} python && ln -fs pip${PYTHON_MINOR_VERSION} pip && \
    find $APP_HOME -type d '(' -name '__pycache__' -o -name 'test' -o -name 'tests' ')' -exec rm -rfv '{}' + && \
    find $APP_HOME -type f '(' -name '*.py[co]' -o -name '*.exe' ')' -exec rm -fv '{}' +  && \
    rm -rf /usr/src/python
    









