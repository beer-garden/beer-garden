APP_NAME="beer-garden"
GROUP=$APP_NAME
USER=$APP_NAME
APP_HOME="/opt/${APP_NAME}"

CONFIG_HOME="$APP_HOME/conf"
LOG_HOME="$APP_HOME/log"
BIN_HOME="$APP_HOME/bin"
PLUGIN_LOG_HOME="$LOG_HOME/plugins"
PLUGIN_HOME="$APP_HOME/plugins"

BARTENDER_CONFIG="${CONFIG_HOME}/bartender-config"
BARTENDER_LOG_CONFIG="${CONFIG_HOME}/bartender-logging-config.json"
BARTENDER_LOG_FILE="$LOG_HOME/bartender.log"

BREW_VIEW_CONFIG="${CONFIG_HOME}/brew-view-config"
BREW_VIEW_LOG_CONFIG="${CONFIG_HOME}/brew-view-logging-config.json"
BREW_VIEW_LOG_FILE="$LOG_HOME/brew-view.log"

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

        # Generate application configs if they don't exist
        # Migrate them if they do, converting to yaml if necessary
        # (.yml will be 'migrated' to .yaml)
        if [ -f "$BARTENDER_CONFIG.yaml" ]; then
            "$APP_HOME/bin/migrate_bartender_config" -c "$BARTENDER_CONFIG.yaml"
        elif [ -f "$BARTENDER_CONFIG.yml" ]; then
            "$APP_HOME/bin/migrate_bartender_config" -c "$BARTENDER_CONFIG.yml"
        elif [ -f "$BARTENDER_CONFIG.json" ]; then
            "$APP_HOME/bin/migrate_bartender_config" -c "$BARTENDER_CONFIG.json" -t "yaml"
        else
            "$APP_HOME/bin/generate_bartender_config" \
                -c "$BARTENDER_CONFIG.yaml" -l "$BARTENDER_LOG_CONFIG" \
                --plugin-local-directory "$PLUGIN_HOME" \
                --plugin-local-log-directory "$PLUGIN_LOG_HOME"
        fi

        if [ -f "$BREW_VIEW_CONFIG.yaml" ]; then
            "$APP_HOME/bin/migrate_brew_view_config" -c "$BREW_VIEW_CONFIG.yaml"
        elif [ -f "$BREW_VIEW_CONFIG.yml" ]; then
            "$APP_HOME/bin/migrate_brew_view_config" -c "$BREW_VIEW_CONFIG.yml"
        elif [ -f "$BREW_VIEW_CONFIG.json" ]; then
            "$APP_HOME/bin/migrate_brew_view_config" -c "$BREW_VIEW_CONFIG.json" -t "yaml"
        else
            "$APP_HOME/bin/generate_brew_view_config" \
                -c "$BREW_VIEW_CONFIG.yaml" -l "$BREW_VIEW_LOG_CONFIG"
        fi

        # Reload units so service is ready to go
        systemctl daemon-reload
    ;;
    2)
        # This is an upgrade, nothing to do
        # Config migration will be done in after_remove
        # See https://github.com/beer-garden/beer-garden/issues/215
    ;;
esac

chown -hR ${USER}:${GROUP} $APP_HOME
