APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"
CONFIG_HOME="${APP_HOME}/conf"
PLUGINS_HOME="${APP_HOME}/plugins"

case "$1" in
    1)
        # This is an initial install.
    ;;
    2)
        # This is an upgrade, so we stop the application first.
        # But we don't want to abort if the service definition is missing
        service $APP_NAME stop || true
    ;;
esac
