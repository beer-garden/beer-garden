FROM python:2-alpine
ARG VERSION

RUN set -ex \
 && pip install --no-cache-dir --pre remote_echo

ENTRYPOINT ["/usr/local/bin/python", "-m", "remote_echo"]

