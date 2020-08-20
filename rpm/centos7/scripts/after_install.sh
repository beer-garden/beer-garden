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
APP_LOG_CONFIG="${CONFIG_HOME}/logging.yaml"
PLUGIN_LOG_CONFIG="${CONFIG_HOME}/plugin-logging.yaml"

APP_LOG_FILE="$LOG_HOME/beer-garden.log"
PLUGIN_LOG_FILE="${PLUGIN_LOG_HOME}/%%(namespace)s/%%(system_name)s-%%(system_version)s/%%(instance_name)s.log"

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

        # Generate application logging config if it doesn't exist
        if [ ! -f "$APP_LOG_CONFIG" ]; then
            "$APP_HOME/bin/generate_app_logging_config" \
                --config-file "$APP_LOG_CONFIG" \
                --filename "$APP_LOG_FILE"
        fi

        # Generate plugin logging config if it doesn't exist
        if [ ! -f "$PLUGIN_LOG_CONFIG" ]; then
            "$APP_HOME/bin/generate_plugin_logging_config" \
                --config-file "$PLUGIN_LOG_CONFIG" \
                --no-stdout \
                --file \
                --filename "$PLUGIN_LOG_FILE"
        fi

        # Generate or migrate application config
        if [ -f "$CONFIG_FILE" ]; then
            "$APP_HOME/bin/migrate_config" -c "$CONFIG_FILE"
        else
            "$APP_HOME/bin/generate_config" \
                -c "$CONFIG_FILE" -l "$APP_LOG_CONFIG" \
                --plugin-local-directory "$PLUGIN_HOME" \
                --plugin-logging-config-file "$PLUGIN_LOG_CONFIG"
        fi

        # Add the UI config file symlinks
        if [ -d "/etc/nginx/conf.d" ]; then
            ln -s "$APP_HOME/ui/conf/conf.d/upstream.conf" "/etc/nginx/conf.d/upstream.conf"
        fi
        if [ -d "/etc/nginx/default.d" ]; then
            ln -s "$APP_HOME/ui/conf/default.d/bg.conf" "/etc/nginx/default.d/bg.conf"
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
