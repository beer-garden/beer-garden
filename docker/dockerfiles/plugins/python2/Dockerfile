FROM alpine:3.9

RUN apk add --no-cache python2 py2-pip && \
    pip --no-cache-dir install -U pip && \
    pip --no-cache-dir install brewtils

WORKDIR /
VOLUME /src

COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "-m", "src"]
