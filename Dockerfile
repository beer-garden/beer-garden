FROM python:3.6-alpine
ARG VERSION
ENTRYPOINT ["bartender"]

ENV BG_PLUGIN_LOCAL_DIRECTORY=/plugins \
    BG_LOG_CONFIG_FILE=/logging-config.json

ADD dev_conf/logging-config.json /logging-config.json

RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
        gcc make musl-dev libffi-dev openssl-dev \
    && pip install --no-cache-dir bartender==$VERSION \
    && apk del .build-deps
