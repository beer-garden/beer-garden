FROM python:2-alpine
ARG VERSION

RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
       gcc make musl-dev libffi-dev openssl-dev \
    && pip install --no-cache-dir brew-view==$VERSION \
    && apk del .build-deps

CMD ["brew-view", "-c", "/config.json"]

