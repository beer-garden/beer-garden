SPECIFICATION = {
    "configuration": {
        "type": "dict",
        "bootstrap": True,
        "items": {
            "file": {
                "type": "str",
                "description": "Path to configuration file to use",
                "required": False,
                "cli_short_name": "c",
                "bootstrap": True,
                "previous_names": ["config"],
                "alt_env_names": ["CONFIG"],
            },
            "type": {
                "type": "str",
                "description": "Configuration file type",
                "required": False,
                "cli_short_name": "t",
                "bootstrap": True,
                "choices": ["json", "yaml"],
            },
        },
    },
    "application": {
        "type": "dict",
        "items": {
            "cors_enabled": {
                "type": "bool",
                "default": False,
                "description": "Determine if CORS should be enabled",
                "previous_names": ["cors_enabled"],
            },
            "debug_mode": {
                "type": "bool",
                "default": False,
                "description": "Run the application in debug mode",
                "previous_names": ["debug_mode"],
            },
            "name": {
                "type": "str",
                "default": "Beer Garden",
                "description": "The title to display on the GUI",
                "previous_names": ["application_name"],
            },
            "icon_default": {
                "type": "str",
                "description": "Default font-awesome icon to display",
                "default": "fa-beer",
                "previous_names": ["icon_default"],
                "alt_env_names": ["ICON_DEFAULT"],
            },
            "allow_unsafe_templates": {
                "type": "bool",
                "default": False,
                "description": "Allow unsafe templates to be loaded by the application",
                "previous_names": [
                    "ALLOW_UNSANITIZED_TEMPLATES",
                    "allow_unsafe_templates",
                ],
                "alt_env_names": [
                    "ALLOW_UNSANITIZED_TEMPLATES",
                    "BG_ALLOW_UNSAFE_TEMPLATES",
                ],
            },
        },
    },
    "auth": {
        "type": "dict",
        "items": {
            "enabled": {
                "type": "bool",
                "default": False,
                "description": "Use role-based authentication / authorization",
            },
            "guest_login_enabled": {
                "type": "bool",
                "default": True,
                "description": "Only applicable if auth is enabled. If set to "
                "true, guests can login without username/passwords.",
            },
            "token": {
                "type": "dict",
                "items": {
                    "algorithm": {
                        "type": "str",
                        "default": "HS256",
                        "description": "Algorithm to use when signing tokens",
                    },
                    "lifetime": {
                        "type": "int",
                        "default": 1200,
                        "description": "Time (seconds) before a token expires",
                    },
                    "secret": {
                        "type": "str",
                        "required": False,
                        "description": "Secret to use when signing tokens",
                        "default": "",
                    },
                },
            },
        },
    },
    "backend": {
        "type": "dict",
        "items": {
            "host": {
                "type": "str",
                "default": "localhost",
                "description": "Backend (Bartender) hostname",
                "previous_names": ["backend_host"],
            },
            "port": {
                "type": "int",
                "default": 9090,
                "description": "Backend (Bartender) thrift port",
                "previous_names": ["backend_port"],
            },
            "socket_timeout": {
                "type": "int",
                "default": 13000,
                "description": "Time (in ms) to wait for backend to respond",
                "previous_names": ["backend_socket_timeout"],
                "previous_defaults": [3000],
            },
        },
    },
    "db": {
        "type": "dict",
        "items": {
            "name": {
                "type": "str",
                "default": "beer_garden",
                "description": "Name of the database to use",
                "previous_names": ["db_name"],
            },
            "connection": {
                "type": "dict",
                "items": {
                    "host": {
                        "type": "str",
                        "default": "localhost",
                        "description": "Hostname/IP of the database server",
                        "previous_names": ["db_host"],
                        "alt_env_names": ["DB_HOST"],
                    },
                    "password": {
                        "type": "str",
                        "default": None,
                        "required": False,
                        "description": "Password to connect to the database",
                        "previous_names": ["db_password"],
                        "alt_env_names": ["DB_PASSWORD"],
                    },
                    "port": {
                        "type": "int",
                        "default": 27017,
                        "description": "Port of the database server",
                        "previous_names": ["db_port"],
                        "alt_env_names": ["DB_PORT"],
                    },
                    "username": {
                        "type": "str",
                        "default": None,
                        "required": False,
                        "description": "Username to connect to the database",
                        "previous_names": ["db_username"],
                        "alt_env_names": ["DB_USERNAME"],
                    },
                },
            },
        },
    },
    "log": {
        "type": "dict",
        "items": {
            "config_file": {
                "type": "str",
                "description": "Path to a logging configuration file",
                "required": False,
                "cli_short_name": "l",
                "previous_names": ["log_config"],
                "alt_env_names": ["LOG_CONFIG"],
            },
            "file": {
                "type": "str",
                "description": "File you would like the application to log to",
                "required": False,
                "previous_names": ["log_file"],
            },
            "level": {
                "type": "str",
                "description": "Log level for the application",
                "default": "INFO",
                "choices": ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"],
                "previous_names": ["log_level"],
            },
        },
    },
    "metrics": {
        "type": "dict",
        "items": {
            "prometheus": {
                "type": "dict",
                "items": {
                    "enabled": {
                        "type": "bool",
                        "description": "Enable prometheus server",
                        "default": True,
                    },
                    "host": {
                        "type": "str",
                        "default": "0.0.0.0",
                        "description": "Host to bind the prometheus server to",
                    },
                    "port": {
                        "type": "int",
                        "description": "Port for prometheus server to listen on.",
                        "default": 2338,
                    },
                    "url": {
                        "type": "str",
                        "description": "URL to prometheus/grafana server.",
                        "required": False,
                    },
                },
            }
        },
    },
    "namespaces": {
        "type": "dict",
        "items": {
            "local": {
                "type": "str",
                "default": "default",
            },
            "remote": {
                "type": "list",
                "required": False,
                "items": {
                    "namespace": {"type": "str"},
                },
            },
        },
    },
    "web": {
        "type": "dict",
        "items": {
            "ssl": {
                "type": "dict",
                "items": {
                    "enabled": {
                        "type": "bool",
                        "default": False,
                        "description": "Serve content using SSL",
                        "previous_names": ["ssl_enabled"],
                        "alt_env_names": ["SSL_ENABLED"],
                        "cli_separator": "_",
                    },
                    "private_key": {
                        "type": "str",
                        "description": "Path to a private key",
                        "required": False,
                        "previous_names": ["ssl_private_key"],
                        "alt_env_names": ["SSL_PRIVATE_KEY"],
                    },
                    "public_key": {
                        "type": "str",
                        "description": "Path to a public key",
                        "required": False,
                        "previous_names": ["ssl_public_key"],
                        "alt_env_names": ["SSL_PUBLIC_KEY"],
                    },
                    "ca_cert": {
                        "type": "str",
                        "description": (
                            "Path to CA certificate file to use for SSLContext"
                        ),
                        "required": False,
                        "previous_names": ["ca_cert"],
                        "alt_env_names": ["CA_CERT"],
                    },
                    "ca_path": {
                        "type": "str",
                        "description": (
                            "Path to CA certificate path to use for SSLContext"
                        ),
                        "required": False,
                        "previous_names": ["ca_path"],
                        "alt_env_names": ["CA_PATH"],
                    },
                    "client_cert_verify": {
                        "type": "str",
                        "description": (
                            "Client certificate mode to use when handling requests"
                        ),
                        "choices": ["NONE", "OPTIONAL", "REQUIRED"],
                        "default": "NONE",
                        "previous_names": ["client_cert_verify"],
                        "alt_env_names": ["CLIENT_CERT_VERIFY"],
                    },
                },
            },
            "port": {
                "type": "int",
                "default": 2337,
                "description": "Serve content on this port",
                "previous_names": ["web_port"],
            },
            "url_prefix": {
                "type": "str",
                "default": None,
                "description": "URL path prefix",
                "required": False,
                "previous_names": ["url_prefix"],
                "alt_env_names": ["URL_PREFIX"],
            },
            "host": {
                "type": "str",
                "default": "0.0.0.0",
                "description": "Host for the HTTP Server to bind to",
            },
            "public_fqdn": {
                "type": "str",
                "default": "localhost",
                "description": "Public fully-qualified domain name",
                "previous_names": ["public_fqdn"],
                "alt_env_names": ["PUBLIC_FQDN"],
            },
        },
    },
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
            "encoding": "utf8",
        }
    else:
        brew_view_handler = {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": level,
            "stream": "ext://sys.stdout",
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
        },
        "handlers": {"brew-view": brew_view_handler},
        "loggers": {
            "tornado.access": {"level": "WARN"},
            "tornado.application": {"level": "WARN"},
            "tornado.general": {"level": "WARN"},
        },
        "root": {"level": level, "handlers": ["brew-view"]},
    }
