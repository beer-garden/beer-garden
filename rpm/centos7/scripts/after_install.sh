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
APP_LOG_CONFIG="${CONFIG_HOME}/app-logging.yaml"
LOCAL_PLUGIN_LOG_CONFIG="${CONFIG_HOME}/local-plugin-logging.yaml"
REMOTE_PLUGIN_LOG_CONFIG="${CONFIG_HOME}/remote-plugin-logging.yaml"

APP_LOG_FILE="$LOG_HOME/beer-garden.log"
PLUGIN_LOG_FILE="${PLUGIN_LOG_HOME}/%%(namespace)s/%%(system_name)s/%%(system_version)s/%%(instance_name)s.log"


# Do this regardless of new install vs upgrade
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

# Migrate old logging config files, if they exist
# This is done for the old config files by after_remove
# This just adds a ".old" extension to them
BARTENDER_LOGGING="${CONFIG_HOME}/bartender-logging-config.json"
if [ -f "$BARTENDER_LOGGING" ]; then
    "$APP_HOME/bin/migrate_bartender_config" -c "$BARTENDER_LOGGING"
fi

BREW_VIEW_LOGGING="${CONFIG_HOME}/brew-view-logging-config.json"
if [ -f "$BREW_VIEW_LOGGING" ]; then
    "$APP_HOME/bin/migrate_brew_view_config" -c "$BREW_VIEW_LOGGING"
fi

# Generate application config if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    "$APP_HOME/bin/generate_config" \
        -c "$CONFIG_FILE" -l "$APP_LOG_CONFIG" \
        --plugin-local-directory "$PLUGIN_HOME" \
        --plugin-local-logging-config-file "$LOCAL_PLUGIN_LOG_CONFIG" \
        --plugin-remote-logging-config-file "$REMOTE_PLUGIN_LOG_CONFIG"
fi

# Generate application logging config if it doesn't exist
if [ ! -f "$APP_LOG_CONFIG" ]; then
    "$APP_HOME/bin/generate_app_logging_config" \
        --config-file "$APP_LOG_CONFIG" \
        --filename "$APP_LOG_FILE"
fi

# Generate plugin logging config if it doesn't exist
if [ ! -f "$REMOTE_PLUGIN_LOG_CONFIG" ] || [ ! -f "$LOCAL_PLUGIN_LOG_CONFIG" ]; then
    "$APP_HOME/bin/generate_plugin_logging_config" \
        --local_conf "$LOCAL_PLUGIN_LOG_CONFIG" \
        --remote_conf "$REMOTE_PLUGIN_LOG_CONFIG" \
        --no-stdout \
        --file \
        --filename "$PLUGIN_LOG_FILE"
fi

# Add the UI config file symlinks
if [ -d "/etc/nginx/conf.d" ] && [ ! -f "/etc/nginx/conf.d/upstream.conf" ]; then
    ln -s "$APP_HOME/ui/conf/conf.d/upstream.conf" "/etc/nginx/conf.d/upstream.conf"
fi
if [ -d "/etc/nginx/default.d" ] && [ ! -f "/etc/nginx/default.d/bg.conf" ]; then
    ln -s "$APP_HOME/ui/conf/default.d/bg.conf" "/etc/nginx/default.d/bg.conf"
fi

# Ensure correct owner and group
chown -hR ${USER}:${GROUP} $APP_HOME

# Reload units
systemctl daemon-reload


# Config migration will be done in after_remove
# See https://github.com/beer-garden/beer-garden/issues/215
