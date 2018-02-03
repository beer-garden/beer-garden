APP_NAME="beer-garden"
APP_HOME="/opt/${APP_NAME}"

case "$1" in
    0)
        # This is an uninstallation of the app, so
        # we don't need to keep anything around anymore.
        if [ -d $APP_HOME/bin ]; then
            rm -rf $APP_HOME/bin
        fi

        if [ -d $APP_HOME/include ]; then
            rm -rf $APP_HOME/include
        fi

        if [ -d $APP_HOME/lib ]; then
            rm -rf $APP_HOME/lib
        fi

        if [ -d $APP_HOME/share ]; then
            rm -rf $APP_HOME/share
        fi

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
