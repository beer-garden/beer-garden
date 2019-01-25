APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"

case "$1" in
    0)
        # This is an uninstallation of the app, so
        # we don't need to keep anything around anymore.
        rm -f /etc/init.d/${APP_NAME}
        /usr/sbin/userdel $APP_NAME
    ;;
    1)
        # This is an upgrade. I think the deletion of files
        # Should be taken care of by the RPM tool itself, so
        # we don't have to do anything in this case.
        :
    ;;
esac
