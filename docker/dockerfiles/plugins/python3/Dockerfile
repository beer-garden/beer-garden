FROM themattrix/pyenv

RUN pyenv local 3.6.0 && \
    python -m pip install -U pip && \
    python -m pip install brewtils

WORKDIR /
VOLUME /src

COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "-m", "src"]
