SPECIFICATION = {
    "amq_admin_host": {
        "type": "string",
        "default": "localhost",
        "description": "Hostname of the AMQ Admin host",
        "previous_names": ["AMQ_ADMIN_HOST"]
    },
    "amq_admin_port": {
        "type": "int",
        "default": 15672,
        "description": "Port of the AMQ Admin host",
        "previous_names": ["AMQ_ADMIN_PORT"]
    },
    "amq_admin_user": {
        "type": "string",
        "default": "guest",
        "description": "Username to login to the AMQ admin",
        "previous_names": ["AMQ_ADMIN_USER"]
    },
    "amq_admin_password": {
        "type": "string",
        "default": "guest",
        "description": "Password to login to the AMQ admin",
        "previous_names": ["AMQ_ADMIN_PW"]
    },
    "amq_connection_attempts": {
        "type": "int",
        "default": 3,
        "description": "Number of retries to connect to AMQ",
        "previous_names": ["AMQ_CONNECTION_ATTEMPTS"]
    },
    "amq_exchange": {
        "type": "string",
        "default": "beer_garden",
        "description": "Exchange name to use for AMQ",
        "previous_names": ["AMQ_EXCHANGE"]
    },
    "amq_heartbeat_interval": {
        "type": "int",
        "default": 3600,
        "description": "Heartbeat interval for AMQ",
        "previous_names": ["AMQ_HEARTBEAT_INTERVAL"]
    },
    "amq_host": {
        "type": "string",
        "default": "localhost",
        "description": "Hostname of AMQ to use",
        "previous_names": ["AMQ_HOST"]
    },
    "amq_port": {
        "type": "int",
        "default": 5672,
        "description": "Port of the AMQ host",
        "previous_names": ["AMQ_PORT"]
    },
    "amq_publish_host": {
        "type": "string",
        "default": "localhost",
        "description": "Publicly accessible hostname for plugins to connect to",
        "previous_names": ["AMQ_PUBLISH_HOST"]
    },
    "amq_password": {
        "type": "string",
        "default": "guest",
        "description": "Password to login to the AMQ host",
        "previous_names": ["AMQ_PW"]
    },
    "amq_user": {
        "type": "string",
        "default": "guest",
        "description": "Username to login to the AMQ host",
        "previous_names": ["AMQ_USER"]
    },
    "amq_virtual_host": {
        "type": "string",
        "default": "/",
        "description": "Virtual host to use for AMQ",
        "previous_names": ["AMQ_VIRTUAL_HOST"]
    },
    "ca_cert": {
        "type": "string",
        "description": "Path to CA certificate file to use",
        "required": False
    },
    "ca_verify": {
        "type": "boolean",
        "default": True,
        "description": "Verify external certificates",
        "required": False
    },
    "config": {
        "type": "string",
        "description": "Path to configuration file to use",
        "required": False,
        "cli_short_name": "c"
    },
    "db_host": {
        "type": "string",
        "default": "localhost",
        "description": "Hostname/IP of the database server",
        "previous_names": ["DB_HOST"]
    },
    "db_name": {
        "type": "string",
        "default": "beer_garden",
        "description": "Name of the database to use",
        "previous_names": ["DB_NAME"]
    },
    "db_password": {
        "type": "string",
        "default": None,
        "required": False,
        "description": "Password to connect to the database"
    },
    "db_port": {
        "type": "int",
        "default": 27017,
        "description": "Port of the database server",
        "previous_names": ["DB_PORT"]
    },
    "db_username": {
        "type": "string",
        "default": None,
        "required": False,
        "description": "Username to connect to the database"
    },
    "event_mongo_ttl": {
        "type": "int",
        "default": 15,
        "description": "Number of minutes to wait before deleting events (negative number for never)"
    },
    "log_config": {
        "type": "string",
        "description": "Path to a logging config file.",
        "required": False,
        "cli_short_name": "l"
    },
    "log_file": {
        "type": "string",
        "description": "File you would like the application to log to",
        "required": False
    },
    "log_level": {
        "type": "string",
        "description": "Log level for the application",
        "default": "INFO",
        "choices": ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"]
    },
    "max_thrift_workers": {
        "type": "int",
        "default": 25,
        "description": "Maximum number of threads available to service incoming thrift calls"
    },
    "action_request_ttl": {
        "type": "int",
        "default": -1,
        "description": "Number of minutes to wait before deleting ACTION requests (negative number for never)"
    },
    "info_request_ttl": {
        "type": "int",
        "default": 15,
        "description": "Number of minutes to wait before deleting INFO request",
        "previous_names": ["INFO_REQUEST_TTL"]
    },
    "plugin_directory": {
        "type": "string",
        "description": "Directory where local plugins are located",
        "required": False,
        "previous_names": ["PLUGINS_DIRECTORY"]
    },
    "plugin_log_directory": {
        "type": "string",
        "description": "Directory where local plugin logs should go",
        "required": False
    },
    "plugin_shutdown_timeout": {
        "type": "int",
        "default": 10,
        "description": "How long to wait for a local plugin to stop before killing it",
        "previous_names": ["PLUGIN_SHUTDOWN_TIMEOUT"]
    },
    "plugin_startup_timeout": {
        "type": "int",
        "default": 5,
        "description": "How long to wait for a local plugin to start before determining it is dead",
        "previous_names": ["PLUGIN_STARTUP_TIMEOUT"]
    },
    "plugin_status_heartbeat": {
        "type": "int",
        "default": 10,
        "description": "Amount of time between status messages"
    },
    "plugin_status_timeout": {
        "type": "int",
        "default": 30,
        "description": "Amount of time to wait before marking a plugin as unresponsive"
    },
    "ssl_enabled": {
        "type": "boolean",
        "default": False,
        "description": "Is the API server using SSL",
        "previous_names": ["SSL_ENABLED"],
        "cli_separator": "_"
    },
    "thrift_host": {
        "type": "string",
        "default": "0.0.0.0",
        "description": "Host to bind the thrift server to"
    },
    "thrift_port": {
        "type": "int",
        "default": 9090,
        "description": "Port to bind the thrift server to",
        "previous_names": ["THRIFT_PORT"]
    },
    "url_prefix": {
        "type": "string",
        "default": None,
        "description": "URL prefix of the API server",
        "required": False
    },
    "web_host": {
        "type": "string",
        "default": "localhost",
        "description": "Hostname of the API server",
        "previous_names": ["WEB_HOST"]
    },
    "web_port": {
        "type": "int",
        "default": 2337,
        "description": "Port of the API server",
        "previous_names": ["WEB_PORT"]
    }
}


def get_default_logging_config(level, filename):
    if filename:
        bartender_handler = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": "simple",
                "filename": filename,
                "maxBytes": 10485760,
                "backupCount": 20,
                "encoding": "utf8"
        }
    else:
        bartender_handler = {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": level,
            "stream": "ext://sys.stdout"
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "bartender": bartender_handler
        },
        "loggers": {
            "pika": {
                "level": "ERROR"
            },
            "requests.packages.urllib3.connectionpool": {
                "level": "WARN"
            }
        },
        "root": {
            "level": level,
            "handlers": ["bartender"]
        }
    }
