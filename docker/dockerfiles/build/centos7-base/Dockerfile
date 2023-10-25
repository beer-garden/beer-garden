# Centos 7 Build Image
#
# This image is for building a CentOS-7/RHEL-7 compatible RPM for beer-garden
#
# It comes with:
#
#  * No Python 
#  * FPM installed for package management
#  * Build essential stuff
#
# Tag: centos7-base

FROM bgio/build:centos7-python3.7

RUN rm python \
    rm pip \
    rm -rf $APP_HOME/bin/python${PYTHON_MINOR_VERSION}

