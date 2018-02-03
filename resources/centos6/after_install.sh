APP_NAME="beer-garden"
GROUP=$APP_NAME
USER=$APP_NAME
APP_HOME="/opt/${APP_NAME}"
PID_HOME="/var/run/${APP_NAME}"

CONFIG_HOME="$APP_HOME/conf"
LOG_HOME="$APP_HOME/log"
BIN_HOME="$APP_HOME/bin"
PLUGIN_LOG_HOME="$LOG_HOME/plugins"
PLUGIN_HOME="$APP_HOME/plugins"

BARTENDER_CONFIG="${CONFIG_HOME}/bartender-config.json"
BARTENDER_LOG_CONFIG="${CONFIG_HOME}/bartender-logging-config.json"
BARTENDER_LOG_FILE="$LOG_HOME/bartender.log"

BREW_VIEW_CONFIG="${CONFIG_HOME}/brew-view-config.json"
BREW_VIEW_LOG_CONFIG="${CONFIG_HOME}/brew-view-logging-config.json"
BREW_VIEW_LOG_FILE="$LOG_HOME/brew-view.log"

case "$1" in
    1)
        # This is an initial install
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

        if [ ! -d "$PID_HOME" ]; then
          mkdir -p "$PID_HOME"
        fi

        # Create the beer-garden group/user if they do not exist
        /usr/bin/getent group $GROUP > /dev/null || /usr/sbin/groupadd -r $GROUP
        /usr/bin/getent passwd $USER > /dev/null || /usr/sbin/useradd -r -d $APP_HOME -s /sbin/nologin -g $GROUP $USER
    ;;
    2)
        # This is an upgrade, nothing to do
    ;;
esac

if [ ! -f "$BARTENDER_LOG_CONFIG" ]; then
  "$APP_HOME/bin/generate_bartender_log_config" \
    --log_config="$BARTENDER_LOG_CONFIG" \
    --log_file="$BARTENDER_LOG_FILE" \
    --log_level="WARN"
fi

if [ ! -f "$BREW_VIEW_LOG_CONFIG" ]; then
  "$APP_HOME/bin/generate_brew_view_log_config" \
    --log_config="$BREW_VIEW_LOG_CONFIG" \
    --log_file="$BREW_VIEW_LOG_FILE" \
    --log_level="WARN"
fi

"$APP_HOME/bin/migrate_bartender_config" -c "$BARTENDER_CONFIG" \
  --log_config="$BARTENDER_LOG_CONFIG" \
  --plugin_directory="$PLUGIN_HOME" \
  --plugin_log_directory="$PLUGIN_LOG_HOME"

"$APP_HOME/bin/migrate_brew_view_config" -c "$BREW_VIEW_CONFIG" \
  --log_config="$BREW_VIEW_LOG_CONFIG"

chown -hR ${USER}:${GROUP} $APP_HOME

# Here we add the beer-garden service script
read -d '' service << EOF
#!/bin/sh
#
# beer-garden    This shell script takes care of starting/stopping beer-garden
#
# chkconfig: - 68 35
# description: Beer Garden Application
# processname: beer-garden
### BEGIN INIT INFO
# Provides: beer-garden
# Short-Description: Beer Garden Application
# Description: Beer Garden Application
### END INIT INFO

# Source function library.
. /etc/rc.d/init.d/functions

BEERGARDEN_HOME="\${BEERGARDEN_HOME:-$APP_HOME}"
PROCESS_NAME="beer-garden"
CONFIG_HOME="\$BEERGARDEN_HOME/conf"

BT_CONFIG_FILE="\$CONFIG_HOME/bartender-config.json"
BT_EXEC="\$BEERGARDEN_HOME/bin/bartender -c \$BT_CONFIG_FILE"
BT_PID_FILE="/var/run/beer-garden/bartender.pid"
BT_LOCK_FILE="/var/lock/subsys/bartender"

BV_CONFIG_FILE="\$CONFIG_HOME/brew-view-config.json"
BV_EXEC="\$BEERGARDEN_HOME/bin/brew-view -c \$BV_CONFIG_FILE"
BV_PID_FILE="/var/run/beer-garden/brew-view.pid"
BV_LOCK_FILE="/var/lock/subsys/brew-view"


start_app() {
  cmd=\$1
  pid_file=\$2
  lock_file=\$3
  process_name=\$4

  # Check to see if the process is running
  running=0
  if [ -f "\$pid_file" ]; then
    pid=\`cat "\$pid_file" 2>/dev/null\`
    if [ -n "\$pid" ]; then
      if [ -d "/proc/\$pid" ]; then
        running=1
      else
        # The process was not running, but was not shut-down successfully.
        # Clean up the pid file
        rm -f "\$pid_file"
      fi
    fi
  fi

  if [ \$running -eq 1 ]; then
    action $"Starting \$process_name" /bin/true
    ret=0
  else
    \$cmd 2>&1 &
    pid=\$!
    ret=0
    sleep 1
    if [ ! -d "/proc/\$pid" ]; then
      echo "Start failed. Check \$process_name application logs"
      ret=1
    fi

    if [ \$ret -eq 0 ]; then
      action $"Starting \$process_name" /bin/true
      echo \$pid > "\$pid_file" 2>/dev/null
      chmod o+r \$pid_file > /dev/null 2>&1
      touch \$lock_file
    else
      action $"Starting \$process_name:" /bin/false
    fi
  fi

  return \$ret

}
start() {

  start_app "\$BV_EXEC" \$BV_PID_FILE \$BV_LOCK_FILE "brew-view"

  # If brew-view doesn't start, no need to start bartender.
  ret=\$?
  if [ \$ret -ne 0 ]; then
    return \$ret
  fi

  start_app "\$BT_EXEC" \$BT_PID_FILE \$BT_LOCK_FILE "bartender"

  return \$?

}

stop_app() {
  pid_file=\$1
  lock_file=\$2
  process_name=\$3

  if [ ! -f "\$pid_file" ]; then
    action $"Stopping \$process_name:" /bin/true
    return 0
  fi

  pid=\`cat "\$pid_file" 2>/dev/null\`
  if [ -n "\$pid_file" ]; then
    /bin/kill -0 \$pid 2>/dev/null
    if [ \$? -eq 0 ]; then
      /bin/kill "\$pid"
    else
      echo "\$process_name already dead."
    fi

    ret=\$?
    if [ \$ret -eq 0 ]; then
      while /bin/kill -0 "\$pid" 2>/dev/null; do
        sleep 0.5
      done
      rm -f \$lock_file
      rm -f \$pid_file
      action $"Stopping \$process_name:" /bin/true
    else
      action $"Stopping \$process_name:" /bin/false
    fi
  else
    action $"Stopping \$process_name:" /bin/false
    ret=4
  fi

  return \$ret
}

stop() {
  stop_app \$BT_PID_FILE \$BT_LOCK_FILE "bartender"
  bt_ret=\$?
  stop_app \$BV_PID_FILE \$BV_LOCK_FILE "brew-view"
  bv_ret=\$?

  if [ \$bt_ret -ne 0 ]; then
    return \$bt_ret
  elif [ \$bv_ret -ne 0 ]; then
    return \$bv_ret
  else
    return 0
  fi
}

restart(){
  stop
  ret=\$?
  if [ \$ret -ne 0 ]; then
    return \$ret
  fi

  start
  return \$?
}

case "\$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    restart
    ;;
  status)
    status -p "\$BT_PID_FILE" "bartender"
    status -p "\$BV_PID_FILE" "brew-view"
    ;;
  *)
    echo "Usage: beer-garden (start|stop|status|restart)"
    exit 2
    ;;
esac

exit \$?
EOF
echo "$service" > /etc/init.d/beer-garden
chmod +x /etc/init.d/beer-garden
