APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"

CONFIG_HOME="$APP_HOME/conf"
CHILDREN_CONFIG_HOME="$CONFIG_HOME/children"
CONFIG_FILE="${CONFIG_HOME}/config.yaml"
APP_LOG_CONFIG="${CONFIG_HOME}/app-logging.yaml"
LOCAL_PLUGIN_LOG_CONFIG="${CONFIG_HOME}/local-plugin-logging.yaml"
REMOTE_PLUGIN_LOG_CONFIG="${CONFIG_HOME}/remote-plugin-logging.yaml"

LOG_HOME="$APP_HOME/log"
PLUGIN_LOG_HOME="$LOG_HOME/plugins"
APP_LOG_FILE="$LOG_HOME/beer-garden.log"
PLUGIN_LOG_FILE="${PLUGIN_LOG_HOME}/%%(namespace)s/%%(system_name)s-%%(system_version)s/%%(instance_name)s.log"

case "$1" in
    0)
        # This is an uninstallation
        # Remove the user
        /usr/sbin/userdel $APP_NAME

        # Remove the UI config file symlinks
        if [ -L "/etc/nginx/conf.d/upstream.conf" ]; then
            unlink "/etc/nginx/conf.d/upstream.conf"
        fi
        if [ -L "/etc/nginx/default.d/bg.conf" ]; then
            unlink "/etc/nginx/default.d/bg.conf"
        fi
    ;;
    1)
        # This is an upgrade.
        # Migrate application config if it exists
        # See https://github.com/beer-garden/beer-garden/issues/215
        if [ -f "$CONFIG_FILE" ]; then
            "$APP_HOME/bin/migrate_config" -c "$CONFIG_FILE"
        fi
    ;;
esac

# Reload units
systemctl daemon-reload
