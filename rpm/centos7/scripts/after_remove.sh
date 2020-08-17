APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"

CONFIG_HOME="$APP_HOME/conf"
LOG_HOME="$APP_HOME/log"

CONFIG_FILE="${CONFIG_HOME}/config.yaml"
LOG_CONFIG="${CONFIG_HOME}/logging.yaml"
LOG_FILE="$LOG_HOME/beer-garden.log"

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
        # Generate logging config if it doesn't exist
        if [ ! -f "$LOG_CONFIG" ]; then
            "$APP_HOME/bin/generate_log_config" \
                --log-config-file "$LOG_CONFIG" \
                --log-file "$LOG_FILE" \
                --log-level "WARN"
        fi

        # Migrate application config if it exists
        if [ -f "$CONFIG_FILE" ]; then
            "$APP_HOME/bin/migrate_config" -c "$CONFIG_FILE"
        fi
    ;;
esac

# Reload units
systemctl daemon-reload
