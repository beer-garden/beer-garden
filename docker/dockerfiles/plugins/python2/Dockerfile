FROM beer-garden/pyenv

RUN pyenv local 2.7.13 && \
    python -m pip install -U pip && \
    python -m pip install brewtils

WORKDIR /
VOLUME /src

COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "-m", "src"]
