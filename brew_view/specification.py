SPECIFICATION = {
    "configuration": {
        'type': 'dict',
        "bootstrap": True,
        'items': {
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
    'amq': {
        'type': 'dict',
        'items': {
            "host": {
                "type": "str",
                "default": "localhost",
                "description": "Hostname of AMQ to use",
                "previous_names": ["amq_host"],
            },
            "heartbeat_interval": {
                "type": "int",
                "default": 3600,
                "description": "Heartbeat interval for AMQ",
                "previous_names": ["amq_heartbeat_interval"],
            },
            "connection_attempts": {
                "type": "int",
                "default": 3,
                "description": "Number of retries to connect to AMQ",
                "previous_names": ["amq_connection_attempts"],
            },
            "exchange": {
                "type": "str",
                "default": "beer_garden",
                "description": "Exchange name to use for AMQ",
                "previous_names": ["amq_exchange"],
            },
            "virtual_host": {
                "type": "str",
                "default": "/",
                "description": "Virtual host to use for AMQ",
                "previous_names": ["amq_virtual_host"],
            },
            'connections': {
                'type': 'dict',
                'items': {
                    'admin': {
                        'type': 'dict',
                        'items': {
                            "port": {
                                "type": "int",
                                "default": 15672,
                                "description": "Port of the AMQ Admin host",
                                "previous_names": ["amq_admin_port"],
                                "alt_env_names": ["AMQ_ADMIN_PORT"],
                            },
                            "user": {
                                "type": "str",
                                "default": "guest",
                                "description": "Username to login to the AMQ admin",
                                "previous_names": ["amq_admin_user"],
                                "alt_env_names": ["AMQ_ADMIN_USER"],
                            },
                            "password": {
                                "type": "str",
                                "default": "guest",
                                "description": "Password to login to the AMQ admin",
                                "previous_names": ["amq_admin_password", "amq_admin_pw"],
                                "alt_env_names": ["AMQ_ADMIN_PASSWORD", "AMQ_ADMIN_PW"],
                            },
                        },
                    },
                    'message': {
                        'type': 'dict',
                        'items': {
                            "port": {
                                "type": "int",
                                "default": 5672,
                                "description": "Port of the AMQ host",
                                "previous_names": ["amq_port"],
                                "alt_env_names": ["AMQ_PORT"],
                            },
                            "password": {
                                "type": "str",
                                "default": "guest",
                                "description": "Password to login to the AMQ host",
                                "previous_names": ["amq_password"],
                                "alt_env_names": ["AMQ_PASSWORD"],
                            },
                            "user": {
                                "type": "str",
                                "default": "guest",
                                "description": "Username to login to the AMQ host",
                                "previous_names": ["amq_user"],
                                "alt_env_names": ["AMQ_USER"],
                            },
                            'ssl': {
                                'type': 'dict',
                                'items': {
                                    "enabled": {
                                        "type": "bool",
                                        "default": False,
                                        "description": "Should the connection use SSL",
                                    },
                                    "ca_cert": {
                                        "type": "str",
                                        "description": "Path to CA certificate file to use",
                                        "required": False,
                                    },
                                    "ca_verify": {
                                        "type": "bool",
                                        "default": True,
                                        "description": "Verify external certificates",
                                        "required": False,
                                    },
                                    "client_cert": {
                                        "type": "str",
                                        "description": "Path to client combined key / certificate",
                                        "required": False,
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },

    "application": {
        'type': 'dict',
        'items': {
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
                "previous_names": ["ALLOW_UNSANITIZED_TEMPLATES", "allow_unsafe_templates"],
                "alt_env_names": ["ALLOW_UNSANITIZED_TEMPLATES", "BG_ALLOW_UNSAFE_TEMPLATES"],
            },
        },
    },

    "auth": {
        'type': 'dict',
        'items': {
            "enabled": {
                "type": "bool",
                "default": False,
                "description": "Use role-based authentication / authorization",
            },
            "token": {
                'type': 'dict',
                'items': {
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

    'backend': {
        'type': 'dict',
        'items': {
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
                "default": 3000,
                "description": "Time (in ms) to wait for backend to respond",
                "previous_names": ["backend_socket_timeout"],
            },
        },
    },

    'db': {
        'type': 'dict',
        'items': {
            "name": {
                "type": "str",
                "default": "beer_garden",
                "description": "Name of the database to use",
                "previous_names": ["db_name"],
            },
            'connection': {
                'type': 'dict',
                'items': {
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
    "cors_enabled": {
        "type": "bool",
        "default": False,
        "description": "Determine if CORS should be enabled",
        "previous_names": ["CORS_ENABLED"],
    },
    "debug_mode": {
        "type": "bool",
        "default": False,
        "description": "Run the application in debug mode",
    },

    'event': {
        'type': 'dict',
        'items': {
            'amq': {
                'type': 'dict',
                'items': {
                    "enable": {
                        "type": "bool",
                        "default": False,
                        "description": "Publish events to RabbitMQ",
                    },
                    "exchange": {
                        "type": "str",
                        "required": False,
                        "description": "Exchange to use for AMQ events",
                        "previous_names": ["event_amq_exchange"],
                    },
                    "virtual_host": {
                        "type": "str",
                        "default": "/",
                        "required": False,
                        "description": "Virtual host to use for AMQ events",
                        "previous_names": ["event_amq_virtual_host"],
                    },
                },
            },
            'mongo': {
                'type': 'dict',
                'items': {
                    "enable": {
                        "type": "bool",
                        "default": True,
                        "description": "Persist events to Mongo",
                        "previous_names": ["event_persist_mongo"],
                        "alt_env_names": ["EVENT_PERSIST_MONGO"],
                    },
                },
            },
        },
    },

    'log': {
        'type': 'dict',
        'items': {
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

    'metrics': {
        'type': 'dict',
        'items': {
            'port': {
                'type': 'int',
                'description': 'Port for prometheus server to listen on.',
                'default': 2338
            },
            'url': {
                'type': 'str',
                'description': 'URL to prometheus/grafana server.',
                'required': False,
            }
        }
    },

    'plugin_logging': {
        'type': 'dict',
        'items': {
            "config_file": {
                "type": "str",
                "description": "Path to a logging configuration file for plugins",
                "required": False,
                "previous_names": ["plugin_log_config"],
                "alt_env_names": ["PLUGIN_LOG_CONFIG"],
            },
            "level": {
                "type": "str",
                "description": "Default log level for plugins (could be "
                               "overwritten by plugin_log_config value)",
                "default": "INFO",
                "choices": ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"],
                "previous_names": ["plugin_log_level"],
                "alt_env_names": ["PLUGIN_LOG_LEVEL"],
            },
        },
    },

    'scheduler': {
        'type': 'dict',
        'items': {
            'auth': {
                'type': 'dict',
                'items': {
                    "username": {
                        "type": "str",
                        "description": "Username that scheduler will use for "
                                       "authentication (needs bg-admin role)",
                        "required": False,
                    },
                    "password": {
                        "type": "str",
                        "description": "Password that scheduler will use for "
                                       "authentication (needs bg-admin role)",
                        "required": False,
                    },
                },
            },
            'max_workers': {
                'type': 'int',
                'default': 10,
                'description': 'Number of workers (processes) to run concurrently.'
            },
            'job_defaults': {
                'type': 'dict',
                'items': {
                    'coalesce': {
                        'type': 'bool',
                        'default': True,
                        'description': (
                            'Should jobs run only once if multiple have missed their window'
                        ),
                    },
                    'max_instances': {
                        'type': 'int',
                        'default': 3,
                        'description': 'Default maximum instances of a job to run concurrently.'
                    }
                }
            }
        }

    },

    'web': {
        'type': 'dict',
        'items': {
            'ssl': {
                'type': 'dict',
                'items': {
                    "enabled": {
                        "type": "bool",
                        "default": False,
                        "description": "Serve content using SSL",
                        "previous_names": ["ssl_enabled"],
                        "alt_env_names": ["SSL_ENABLED"],
                        "cli_separator": "_"
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
                        "description": "Path to CA certificate file to use for SSLContext",
                        "required": False,
                        "previous_names": ["ca_cert"],
                        "alt_env_names": ["CA_CERT"],
                    },
                    "ca_path": {
                        "type": "str",
                        "description": "Path to CA certificate path to use for SSLContext",
                        "required": False,
                        "previous_names": ["ca_path"],
                        "alt_env_names": ["CA_PATH"],
                    },
                    "client_cert_verify": {
                        "type": "str",
                        "description": "Client certificate mode to use when handling requests",
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
            'host': {
                'type': 'str',
                'default': '0.0.0.0',
                'description': 'Host for the HTTP Server to bind to',
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

    "shutdown_timeout": {
        "type": "int",
        "default": 5,
        "description": "How long to wait for Brew View to shutdown before terminating",
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
