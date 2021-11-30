FROM python:3.8-alpine
ARG VERSION
ENTRYPOINT ["beergarden"]

ENV BG_LOG_CONFIG_FILE=/conf/app-logging.yaml \
    BG_PLUGIN_LOCAL_LOGGING_CONFIG_FILE=/conf/local-plugin-logging.yaml \
    BG_PLUGIN_REMOTE_LOGGING_CONFIG_FILE=/conf/remote-plugin-logging.yaml \
    BG_PLUGIN_LOCAL_DIRECTORY=/plugins

ADD example_configs/app-logging.yaml /conf/
ADD example_configs/local-plugin-logging.yaml /conf/
ADD example_configs/remote-plugin-logging.yaml /conf/

RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
       gcc make musl-dev libffi-dev openssl-dev alpine-conf \
    && setup-timezone -z UTC \
    && pip install --no-cache-dir beer-garden==$VERSION \
    && apk del .build-deps
