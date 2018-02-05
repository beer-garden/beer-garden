FROM python:2-alpine
ARG VERSION

RUN set -ex \
    && pip install --no-cache-dir brew-view==$VERSION

CMD ["brew-view", "-c", "/config.json"]

