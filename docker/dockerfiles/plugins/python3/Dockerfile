FROM beer-garden/pyenv

RUN pyenv local 3.6.1 && \
    python -m pip install -U pip && \
    python -m pip install brewtils

WORKDIR /
VOLUME /src

COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "-m", "src"]
