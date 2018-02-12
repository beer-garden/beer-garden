
SPECIFICATION = {
    "allow_unsafe_templates": {
        "type": "bool",
        "default": False,
        "description": "Allow unsafe templates to be loaded by the application",
        "previous_names": ["ALLOW_UNSANITIZED_TEMPLATES"]
    },
    "amq_admin_host": {
        "type": "str",
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
        "type": "str",
        "default": "guest",
        "description": "Username to login to the AMQ admin",
        "previous_names": ["AMQ_ADMIN_USER"]
    },
    "amq_admin_password": {
        "type": "str",
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
    "amq_host": {
        "type": "str",
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
    "amq_password": {
        "type": "str",
        "default": "guest",
        "description": "Password to login to the AMQ host",
        "previous_names": ["AMQ_PW"]
    },
    "amq_user": {
        "type": "str",
        "default": "guest",
        "description": "Username to login to the AMQ host",
        "previous_names": ["AMQ_USER"]
    },
    "amq_virtual_host": {
        "type": "str",
        "default": "/",
        "description": "Virtual host to use for AMQ",
        "previous_names": ["AMQ_VIRTUAL_HOST"]
    },
    "application_name": {
        "type": "str",
        "default": "Beer Garden",
        "description": "The title to display on the GUI",
        "previous_names": ["APPLICATION_NAME"]
    },
    "backend_host": {
        "type": "str",
        "default": "localhost",
        "description": "The hostname of the backend server",
        "previous_names": ["BACKEND_HOST"]
    },
    "backend_port": {
        "type": "int",
        "default": 9090,
        "description": "The port the backend server is bound to",
        "previous_names": ["BACKEND_PORT"]
    },
    "backend_socket_timeout": {
        "type": "int",
        "default": 3000,
        "description": "Time (in ms) to wait for backend to respond"
    },
    "config": {
        "type": "str",
        "description": "Path to configuration file to use",
        "required": False,
        "cli_short_name": "c"
    },
    "cors_enabled": {
        "type": "bool",
        "default": False,
        "description": "Determine if CORS should be enabled",
        "previous_names": ["CORS_ENABLED"]
    },
    "db_host": {
        "type": "str",
        "default": "localhost",
        "description": "Hostname/IP of the database server",
        "previous_names": ["DB_HOST"]
    },
    "db_name": {
        "type": "str",
        "default": "beer_garden",
        "description": "Name of the database to use",
        "previous_names": ["DB_NAME"]
    },
    "db_password": {
        "type": "str",
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
        "type": "str",
        "default": None,
        "required": False,
        "description": "Username to connect to the database"
    },
    "debug_mode": {
        "type": "bool",
        "default": False,
        "description": "Run the application in debug mode (used mostly for development)"
    },
    "event_amq_exchange": {
        "type": "str",
        "required": False,
        "description": "Exchange to use for AMQ events"
    },
    "event_amq_virtual_host": {
        "type": "str",
        "default": "/",
        "required": False,
        "description": "Virtual host to use for AMQ events"
    },
    "event_persist_mongo": {
        "type": "bool",
        "default": True,
        "description": "Publish events to Mongo"
    },
    "icon_default": {
        "type": "str",
        "description": "Default font-awesome icon to display",
        "default": "fa-beer"
    },
    "log_config": {
        "type": "str",
        "description": "Path to a logging config file.",
        "required": False,
        "cli_short_name": "l"
    },
    "log_file": {
        "type": "str",
        "description": "File you would like the application to log to",
        "required": False
    },
    "log_level": {
        "type": "str",
        "description": "Log level for the application",
        "default": "INFO",
        "choices": ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"]
    },
    "plugin_log_config": {
        "type": "str",
        "description": "Path to a logging config for plugins.",
        "required": False
    },
    "plugin_log_level": {
        "type": "str",
        "description": "Default log level for plugins (could be "
                       "overwritten by plugin_log_config value)",
        "default": "INFO",
        "choices": ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"]
    },
    "public_fqdn": {
        "type": "str",
        "default": "localhost",
        "description": "Public fully-qualified domain name"
    },
    "shutdown_timeout": {
        "type": "int",
        "default": 5,
        "description": "How long to wait for Brew View to shutdown before terminating"
    },
    "ssl_enabled": {
        "type": "bool",
        "default": False,
        "description": "Should we use SSL on start-up",
        "previous_names": ["SSL_ENABLED"],
        "cli_separator": "_"
    },
    "ssl_private_key": {
        "type": "str",
        "description": "Path to a private key",
        "required": False,
        "previous_names": ["SSL_PRIVATE_KEY"]
    },
    "ssl_public_key": {
        "type": "str",
        "description": "Path to a public key",
        "required": False,
        "previous_names": ["SSL_PUBLIC_KEY"]
    },
    "url_prefix": {
        "type": "str",
        "default": None,
        "description": "URL path prefix",
        "required": False
    },
    "web_port": {
        "type": "int",
        "default": 2337,
        "description": "Port to bind to",
        "previous_names": ["WEB_PORT"]
    }
}


def get_default_logging_config(level, filename):
    if filename:
        brew_view_handler = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": "simple",
                "filename": filename,
                "maxBytes": 10485760,
                "backupCount": 20,
                "encoding": "utf8"
        }
    else:
        brew_view_handler = {
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
            "brew-view": brew_view_handler
        },
        "loggers": {
            "tornado.access": {
                "level": "WARN"
            },
            "tornado.application": {
                "level": "WARN"
            },
            "tornado.general": {
                "level": "WARN"
            }
        },
        "root": {
            "level": level,
            "handlers": ["brew-view"]
        }
    }
