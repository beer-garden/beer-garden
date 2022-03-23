FROM alpine:3.9

RUN apk add --no-cache "python3<3.7" && \
    pip3 --no-cache-dir install -U pip && \
    pip3 --no-cache-dir install brewtils && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    ls -s /usr/bin/pip3 /usr/bin/pip

WORKDIR /
VOLUME /src

COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "-m", "src"]
