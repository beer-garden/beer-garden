ARG PYTHON_IMAGE=python:3.12-slim
FROM $PYTHON_IMAGE
ARG VERSION

ENV BG_LOG_CONFIG_FILE=/conf/app-logging.yaml \
    BG_PLUGIN_LOCAL_LOGGING_CONFIG_FILE=/conf/local-plugin-logging.yaml \
    BG_PLUGIN_REMOTE_LOGGING_CONFIG_FILE=/conf/remote-plugin-logging.yaml \
    BG_PLUGIN_LOCAL_DIRECTORY=/plugins \
    BG_CHILDREN_CONFIG_DIRECTORY=/conf/children

ADD ./requirements.txt .

RUN set -ex \
    && apt-get -y update \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir beer-garden==$VERSION \
    && mkdir -p /conf/children

ADD example_configs/app-logging.yaml /conf/
ADD example_configs/local-plugin-logging.yaml /conf/
ADD example_configs/remote-plugin-logging.yaml /conf/
ADD docker/docker-entrypoint.sh /usr/local/bin/

EXPOSE 2337/tcp
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Using standard OCI (Open Container Initiative)
LABEL version="$VERSION" \
      description="Beer Garden" \
      source="https://github.com/beer-garden/beer-garden" \
      maintainer="Beer Garden Maintainers" \
      org.opencontainers.image.title="Beer Garden" \
      org.opencontainers.image.source="https://github.com/beer-garden/beer-garden" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.authors="Beer Garden Maintainers" \ 
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.url="https://beer-garden.io/" \
      org.opencontainers.image.documentation="https://beer-garden.io/"