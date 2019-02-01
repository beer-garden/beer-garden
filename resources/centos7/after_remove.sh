APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"

CONFIG_HOME="$APP_HOME/conf"
LOG_HOME="$APP_HOME/log"

BARTENDER_CONFIG="${CONFIG_HOME}/bartender-config"
BARTENDER_LOG_CONFIG="${CONFIG_HOME}/bartender-logging-config.json"
BARTENDER_LOG_FILE="$LOG_HOME/bartender.log"

BREW_VIEW_CONFIG="${CONFIG_HOME}/brew-view-config"
BREW_VIEW_LOG_CONFIG="${CONFIG_HOME}/brew-view-logging-config.json"
BREW_VIEW_LOG_FILE="$LOG_HOME/brew-view.log"

case "$1" in
    0)
        # This is an uninstallation
        # Remove the user
        /usr/sbin/userdel $APP_NAME
    ;;
    1)
        # This is an upgrade.
        # Migrate config files if they exist
        if [ -f "$BARTENDER_CONFIG.yml" ]; then
            "$APP_HOME/bin/migrate_bartender_config" -c "$BARTENDER_CONFIG.yml"
        elif [ -f "$BARTENDER_CONFIG.json" ]; then
            "$APP_HOME/bin/migrate_bartender_config" -c "$BARTENDER_CONFIG.json"
        fi

        if [ -f "$BREW_VIEW_CONFIG.yml" ]; then
            "$APP_HOME/bin/migrate_brew_view_config" -c "$BREW_VIEW_CONFIG.yml"
        elif [ -f "$BREW_VIEW_CONFIG.json" ]; then
            "$APP_HOME/bin/migrate_brew_view_config" -c "$BREW_VIEW_CONFIG.json"
        fi
    ;;
esac

# Remove the old sysV init script if it exists
if [ -f /etc/init.d/${APP_NAME} ]; then
    rm -f /etc/init.d/${APP_NAME}
fi

# And reload units
systemctl daemon-reload
