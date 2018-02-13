FROM python:2-alpine
ARG VERSION

ADD dist/bartender-$VERSION-py2.py3-none-any.whl /root/

RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
        gcc make musl-dev libffi-dev openssl-dev \
    # && pip install --no-cache-dir bartender==$VERSION \
    && pip install --no-cache-dir /root/bartender-$VERSION-py2.py3-none-any.whl \
    && apk del .build-deps

CMD ["bartender", "-c", "/config.json"]
