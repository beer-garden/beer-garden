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
        # Generate logging configs if they don't exist
        if [ ! -f "$BARTENDER_LOG_CONFIG" ]; then
            "$APP_HOME/bin/generate_bartender_log_config" \
                --log-config-file "$BARTENDER_LOG_CONFIG" \
                --log-file "$BARTENDER_LOG_FILE" \
                --log-level "WARN"
        fi

        if [ ! -f "$BREW_VIEW_LOG_CONFIG" ]; then
            "$APP_HOME/bin/generate_brew_view_log_config" \
                --log-config-file "$BREW_VIEW_LOG_CONFIG" \
                --log-file "$BREW_VIEW_LOG_FILE" \
                --log-level "WARN"
        fi

        # Enforce .yaml extension for yaml config files
        if [ -f "$BARTENDER_CONFIG.yml" ]; then
            mv "$BARTENDER_CONFIG.yml" "$BARTENDER_CONFIG.yaml"
        fi
        if [ -f "$BREW_VIEW_CONFIG.yml" ]; then
            mv "$BREW_VIEW_CONFIG.yml" "$BREW_VIEW_CONFIG.yaml"
        fi

        # Migrate config files if they exist, converting to yaml if necessary
        if [ -f "$BARTENDER_CONFIG.yaml" ]; then
            "$APP_HOME/bin/migrate_bartender_config" -c "$BARTENDER_CONFIG.yaml"
        elif [ -f "$BARTENDER_CONFIG.json" ]; then
            "$APP_HOME/bin/migrate_bartender_config" -c "$BARTENDER_CONFIG.json" -t "yaml"
        fi

        if [ -f "$BREW_VIEW_CONFIG.yaml" ]; then
            "$APP_HOME/bin/migrate_brew_view_config" -c "$BREW_VIEW_CONFIG.yaml"
        elif [ -f "$BREW_VIEW_CONFIG.json" ]; then
            "$APP_HOME/bin/migrate_brew_view_config" -c "$BREW_VIEW_CONFIG.json" -t "yaml"
        fi
    ;;
esac
