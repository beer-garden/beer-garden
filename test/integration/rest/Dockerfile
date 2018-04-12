FROM python:2-alpine

WORKDIR /usr/src/app
VOLUME ["/usr/src/app/"]

ADD requirements.txt /usr/src/app/requirements.txt

RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
        gcc musl-dev \
    && pip install --no-cache-dir -r /usr/src/app/requirements.txt \
    && apk del .build-deps
