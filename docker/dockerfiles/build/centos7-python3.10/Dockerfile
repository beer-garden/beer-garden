# Centos 7 Build Image
#
# This image is for building a CentOS-7/RHEL-7 compatible RPM for beer-garden
#
# It comes with:
#
#  * Python 3.9.18 installed
#  * FPM installed for package management
#  * Build essential stuff
#
# Tag: centos7-python3.9

FROM bgio/build:centos7-base

ENV LANG=en_US.UTF-8 \
    PYTHON_VERSION=3.10.13 \
    PYTHON_MINOR_VERSION=3.10 \
    APP_HOME=/opt/beer-garden

RUN mkdir -p /usr/src/python && \
    curl https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz -o Python-${PYTHON_VERSION}.tar.xz && \
    tar -xC /usr/src/python/ --strip-components=1 -f Python-${PYTHON_VERSION}.tar.xz && \
    rm -f Python-${PYTHON_VERSION}.tar.xz && \
    cd /usr/src/python && \
    ./configure --prefix=$APP_HOME && \
    make altinstall prefix=$APP_HOME exec-prefix=$APP_HOME && \
    $APP_HOME/bin/python${PYTHON_MINOR_VERSION} -m "ensurepip" && \
    cd $APP_HOME/bin && \
    ln -fs python${PYTHON_MINOR_VERSION} python && ln -fs pip${PYTHON_MINOR_VERSION} pip && \
    find $APP_HOME -type d '(' -name '__pycache__' -o -name 'test' -o -name 'tests' ')' -exec rm -rfv '{}' + && \
    find $APP_HOME -type f '(' -name '*.py[co]' -o -name '*.exe' ')' -exec rm -fv '{}' + && \
    rm -rf /usr/src/python

