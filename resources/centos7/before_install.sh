APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"
CONFIG_HOME="${APP_HOME}/conf"
PLUGINS_HOME="${APP_HOME}/plugins"
OLD_APP_HOME="/apps/${APP_NAME}"

case "$1" in
    1)
        # This is an initial install. For convenience, if they had the
        # bartender/brew-view RPMs already installed, we will move over
        # the config for them.

        mkdir -p $CONFIG_HOME

        if [ -f "$OLD_APP_HOME/conf/bartender-config.json" ]; then
            cp "$OLD_APP_HOME/conf/bartender-config.json" $CONFIG_HOME
        fi

        if [ -f "$OLD_APP_HOME/conf/bartender-logging-config.json" ]; then
            cp "$OLD_APP_HOME/conf/bartender-logging-config.json" $CONFIG_HOME
        fi

        if [ -f "$OLD_APP_HOME/conf/brew-view-config.json" ]; then
            cp "$OLD_APP_HOME/conf/brew-view-config.json" $CONFIG_HOME
        fi

        if [ -f "$OLD_APP_HOME/conf/brew-view-logging-config.json" ]; then
            cp "$OLD_APP_HOME/conf/brew-view-logging-config.json" $CONFIG_HOME
        fi

        if [ -d "$OLD_APP_HOME/plugins" ]; then
            cp -R "$OLD_APP_HOME/plugins" $APP_HOME
        fi

    ;;
    2)
        # This is an upgrade, so we stop the application first.
        systemctl stop $APP_NAME
    ;;
esac
