FROM python:alpine

WORKDIR /src
COPY remote_echo ./remote_echo
COPY setup.py .

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "remote_echo"]
