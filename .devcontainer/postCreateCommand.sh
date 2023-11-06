#!/bin/sh

cd /workspaces/beer-garden/src/app/;
pip install -r requirements.txt;

cd /workspaces/beer-garden/src/ui/;
make deps;

cd /workspaces/beer-garden/docker/docker-compose;
docker-compose up -d mongodb rabbitmq;
