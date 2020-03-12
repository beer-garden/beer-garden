FROM python:3.7-alpine
ARG VERSION
ENTRYPOINT ["beergarden"]

ENV BG_PLUGIN_LOCAL_DIRECTORY=/plugins \
    BG_LOG_CONFIG_FILE=/logging-config.yaml

ADD example_configs/logging-config.yaml /logging-config.yaml

RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
       gcc make musl-dev libffi-dev openssl-dev \
    && pip install --no-cache-dir beer-garden==$VERSION \
    && apk del .build-deps
