FROM python:2-alpine
ARG VERSION

RUN set -ex \
    && apk add --no-cache --virtual .app-build-deps \
        gcc make musl-dev libffi-dev openssl-dev \
    && pip install --no-cache-dir bartender==$VERSION \
    && apk del .app-build-deps

CMD ["bartender", "-c", "/config.json"]
