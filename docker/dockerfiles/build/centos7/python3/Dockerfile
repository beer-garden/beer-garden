FROM centos:7

ENV LANG=en_US.UTF-8 \
    PYTHON_VERSION=3.6.5 \
    PYTHON_MINOR_VERSION=3.6 \
    APP_HOME=/opt/beer-garden

RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 && \
    yum install -y \
        gcc \
        gcc-c++ \
        zlib \
        zlib-devel \
        curl-devel \
        libffi-devel \
        openssl-devel \
        readline-devel \
        rpm-build \
        tar \
        make \
        bzip2-devel \
        sqlite-devel \
        ruby-devel \
        rubygems && \
    gem install --no-ri --no-rdoc fpm && \
    mkdir -p /usr/src/python && \
    mkdir -p $APP_HOME && \
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

