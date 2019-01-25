APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"

# These files will have been created after installation so they aren't
# 'owned' by the rpm. So we need to remove them before uninstalling or
# upgrading so we don't have extra files / empty directories hanging around
find $APP_HOME -name '*.pyc' -exec rm -f {} +
find $APP_HOME -name '*.pyo' -exec rm -f {} +
find $APP_HOME -name '__pycache__' -exec rm -fr {} +

case "$1" in
    0)
        # This is an uninstallation.
        systemctl stop $APP_NAME
        systemctl disable $APP_NAME
    ;;
    1)
        # This is an upgrade.
        # Do nothing because the pre install scripts will
        # Take care of it.
        :
    ;;
esac
