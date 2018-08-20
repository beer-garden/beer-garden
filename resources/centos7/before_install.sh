APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"
CONFIG_HOME="${APP_HOME}/conf"
PLUGINS_HOME="${APP_HOME}/plugins"

case "$1" in
    1)
        # This is an initial install. Version migrations should go here
    ;;
    2)
        # This is an upgrade, so we stop the application first.
        systemctl stop $APP_NAME
    ;;
esac
