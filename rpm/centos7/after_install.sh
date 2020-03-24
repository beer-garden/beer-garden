APP_NAME="beer-garden"
GROUP=$APP_NAME
USER=$APP_NAME
APP_HOME="/opt/${APP_NAME}"

CONFIG_HOME="$APP_HOME/conf"
LOG_HOME="$APP_HOME/log"
BIN_HOME="$APP_HOME/bin"
PLUGIN_LOG_HOME="$LOG_HOME/plugins"
PLUGIN_HOME="$APP_HOME/plugins"

CONFIG_FILE="${CONFIG_HOME}/config.yaml"
LOG_CONFIG="${CONFIG_HOME}/logging.yaml"
LOG_FILE="$LOG_HOME/beer-garden.log"

case "$1" in
    1)
        # This is an initial install
        # Create the beer-garden group/user if they do not exist
        /usr/bin/getent group $GROUP > /dev/null || /usr/sbin/groupadd -r $GROUP
        /usr/bin/getent passwd $USER > /dev/null || /usr/sbin/useradd -r -d $APP_HOME -s /sbin/nologin -g $GROUP $USER

        if [ ! -d "$CONFIG_HOME" ]; then
            mkdir -p "$CONFIG_HOME"
        fi
        if [ ! -d "$LOG_HOME" ]; then
            mkdir -p "$LOG_HOME"
        fi
        if [ ! -d "$PLUGIN_LOG_HOME" ]; then
            mkdir -p "$PLUGIN_LOG_HOME"
        fi
        if [ ! -d "$PLUGIN_HOME" ]; then
            mkdir -p "$PLUGIN_HOME"
        fi

        # Generate logging config if it doesn't exist
        if [ ! -f "$LOG_CONFIG" ]; then
            "$APP_HOME/bin/generate_log_config" \
                --log-config-file "$LOG_CONFIG" \
                --log-file "$LOG_FILE" \
                --log-level "WARN"
        fi

        # Generate or migrate application config
        if [ -f "$CONFIG_FILE" ]; then
            "$APP_HOME/bin/migrate_config" -c "$CONFIG_FILE"
        else
            "$APP_HOME/bin/generate_config" \
                -c "$CONFIG_FILE" -l "$LOG_CONFIG" \
                --plugin-local-directory "$PLUGIN_HOME" \
                --plugin-local-log-directory "$PLUGIN_LOG_HOME"
        fi

        # Reload units
        systemctl daemon-reload
    ;;
    2)
        # This is an upgrade, nothing to do
        # Config migration will be done in after_remove
        # See https://github.com/beer-garden/beer-garden/issues/215
    ;;
esac

chown -hR ${USER}:${GROUP} $APP_HOME
