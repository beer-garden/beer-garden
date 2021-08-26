FROM python:3.8.11-bullseye

ENV _BEER_GARDEN_HOME /beer_garden
ENV _BEER_GARDEN_APP_HOME $_BEER_GARDEN_HOME/src/app
VOLUME $_BEER_GARDEN_HOME

ENV _BREWTILS_HOME /brewtils
VOLUME $_BREWTILS_HOME

ENV CONF_DIR=/conf

# This is an unfortunate work-around. TODO
ARG PLUGINS_SHA1=12d3e5d
ARG PLUGINS_LINK=https://github.com/beer-garden/example-plugins/tarball/master

ENV BG_LOG_CONFIG_FILE=/conf/app-logging.yaml \
    BG_PLUGIN_LOGGING_CONFIG_FILE=/conf/plugin-logging.yaml \
    BG_PLUGIN_LOCAL_DIRECTORY=/plugins

COPY configs/app-logging.yaml $CONF_DIR/
COPY configs/plugin-logging.yaml $CONF_DIR/
COPY configs/config.yaml $CONF_DIR/
COPY requirements.txt $CONF_DIR/

RUN set -ex \
    \
    && pip install -r $CONF_DIR/requirements.txt

WORKDIR /
RUN curl -sL $PLUGINS_LINK | tar xz \
    && ln -s beer-garden-example-plugins-$PLUGINS_SHA1 $BG_PLUGIN_LOCAL_DIRECTORY

CMD pip install -e $_BREWTILS_HOME && python $_BEER_GARDEN_APP_HOME/bin/app.py -c $CONF_DIR/config.yaml -l $CONF_DIR/app-logging.yaml