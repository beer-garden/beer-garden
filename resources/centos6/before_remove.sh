APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"

case "$1" in
    0)
        # This is an uninstallation.
        service $APP_NAME stop
        chkconfig --del $APP_NAME
    ;;
    1)
        # This is an upgrade.
        # Do nothing because the pre install scripts will
        # Take care of it.
        :
    ;;
esac
