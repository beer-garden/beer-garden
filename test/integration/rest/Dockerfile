FROM python:2-alpine

VOLUME ["/usr/src/app/"]
ADD requirements.txt /usr/src/app/requirements.txt
RUN set -ex \
    && apk add --no-cache --update-cache --virtual .app-build-deps \
            gcc \
            musl-dev \
    && pip install --no-cache-dir -r /usr/src/app/requirements.txt
WORKDIR /usr/src/app
