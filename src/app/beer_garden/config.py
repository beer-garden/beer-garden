# -*- coding: utf-8 -*-
"""Config Service

The configuration service is responsible for:

* Loading configuration files
* Migration configuration files between Beer Garden versions
* Getting configuration values
"""
import os
import sys
from argparse import ArgumentParser
from datetime import datetime
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from box import Box
from brewtils.rest import normalize_url_prefix as normalize
from ruamel.yaml import YAML
from yapconf import YapconfSpec, dump_data

from beer_garden.errors import ConfigurationError
from beer_garden.log import default_app_config, default_plugin_config

__all__ = [
    "load",
    "generate_app_logging",
    "generate_plugin_logging",
    "generate",
    "migrate",
    "get",
]

_CONFIG = None


def load(args: Sequence[str], force: bool = False) -> None:
    """Load the application configuration.

    Attempt to load the application configuration in the following order:

    1. CLI Arguments
    2. File (specified either by CLI or environment variable)
    3. Environment variables

    If force is True then it will always reload the configuration, otherwise
    if the configuration is already loaded, will immediately return.

    Once loaded, the configuration can be reached with the `get` method.

    Args:
        args: Command line arguments
        force: Force a reload
    """
    global _CONFIG
    if _CONFIG is not None and not force:
        return

    spec, cli_vars = _parse_args(args)
    config_sources = _setup_config_sources(spec, cli_vars)

    raw_config = spec.load_config(*config_sources)

    # Create a Box with default to avoid KeyErrors
    config = Box(raw_config.to_dict(), default_box=True)
    if config.entry.http.url_prefix:
        config.entry.http.url_prefix = normalize(config.entry.http.url_prefix)

    _CONFIG = Box(config.to_dict())


def generate(args: Sequence[str]):
    """Generate a configuration file.

    Takes a series of command line arguments and will create a file at the location
    specified by the resolved `configuration.file` value. If that value resolves to None
    the configuration will be printed to STDOUT.

    Note that bootstrap items will not be included in the generated configuration.

    Args:
        args: Command line arguments

    Returns:
        None

    Raises:
        YapconfLoadError: Missing 'config' configuration option (file location)
    """
    spec, cli_vars = _parse_args(args)

    bootstrap = spec.load_filtered_config(cli_vars, "ENVIRONMENT", bootstrap=True)
    config = spec.load_filtered_config(cli_vars, "ENVIRONMENT", exclude_bootstrap=True)

    dump_data(config, filename=bootstrap.configuration.file, file_type="yaml")


def migrate(args: Sequence[str]):
    """Updates a configuration file in-place.

    Args:
        args: Command line arguments. Must contain an argument that specifies the
        config file to update ('-c')
    Returns:
        None

    Raises:
        YapconfLoadError: Missing 'config' configuration option (file location)
    """
    spec, cli_vars = _parse_args(args)

    config = spec.load_config(cli_vars, "ENVIRONMENT")

    if not config.configuration.file:
        raise SystemExit(
            "Please specify a config file to update in the CLI arguments (-c)"
        )

    current_root, current_extension = os.path.splitext(config.configuration.file)

    current_type = current_extension[1:]
    if current_type == "yml":
        current_type = "yaml"

    # Determine if a type conversion is needed
    type_conversion = False
    new_type = "yaml"
    if current_type != new_type:
        new_file = current_root + "." + new_type
        type_conversion = True
    else:
        new_file = config.configuration.file

    spec.migrate_config_file(
        config.configuration.file,
        current_file_type=current_type,
        output_file_name=new_file,
        output_file_type=new_type,
        update_defaults=True,
        include_bootstrap=False,
    )

    if type_conversion:
        os.remove(config.configuration.file)


def generate_app_logging(args: Sequence[str]):
    """Generate and save application logging configuration file.

    Args:
        args: Command line arguments
            --config-file: Configuration will be written to this file (will print to
                stdout if missing)
            --filename: Logs will be written to this file (if file logging is enabled)
            --level: Log level to use

    Returns:
        Logging configuration in dict form
    """
    parser = ArgumentParser()
    parser.add_argument("--config-file", type=str, default=None)
    parser.add_argument("--level", type=str, default=None)
    parser.add_argument("--filename", type=str, default=None)

    parsed_args = vars(parser.parse_args(args))

    logging_config = default_app_config(
        parsed_args.get("level"), parsed_args.get("filename")
    )

    dump_data(logging_config, filename=parsed_args.get("config_file"), file_type="yaml")

    return logging_config


def generate_plugin_logging(args: Sequence[str]) -> dict:
    """Generate and save plugin logging configuration file.

    Args:
        args: Command line arguments
            --config-file: Plugin configuration will be written to this file (will print to
                stdout if missing)
            --stdout: Explicitly enable logging to stdout
            --no-stdout: Explicitly disable logging to stdout
            --file: Explicitly enable logging to a file
            --no-file: Explicitly disable logging to a file
            --filename: Logs will be written to this file (if file logging is enabled)
            --level: Log level to use

    Returns:
        Logging configuration in dict form
    """
    parser = ArgumentParser()
    parser.add_argument("--config-file", type=str, default=None)
    parser.add_argument("--level", type=str, default=None)
    parser.add_argument("--filename", type=str, default=None)

    parser.add_argument("--stdout", dest="stdout", action="store_true")
    parser.add_argument("--no-stdout", dest="stdout", action="store_false")

    parser.add_argument("--file", dest="file", action="store_true")
    parser.add_argument("--no-file", dest="file", action="store_false")

    parsed_args = vars(parser.parse_args(args))

    logging_config = default_plugin_config(
        level=parsed_args.get("level"),
        stdout=parsed_args.get("stdout"),
        file=parsed_args.get("file"),
        filename=parsed_args.get("filename"),
    )

    dump_data(logging_config, filename=parsed_args.get("config_file"), file_type="yaml")

    return logging_config


def get(key: Optional[str] = None) -> Union[str, int, float, bool, complex, Box, None]:
    """Get specified key from the config.

    Nested keys can be separated with a "." If the key does not exist, then
    a None will be returned.

    If the key itself is None, then the entire config will be returned.

    If the requested value is a container (has child items) then the returned value will
    be an immutable (frozen) ``box.Box`` object.

    Args:
        key: The key to get, nested keys are separated with "."

    Returns:
        The value of the key in the config.
    """
    if key is None:
        return _CONFIG

    value = _CONFIG
    for key_part in key.split("."):
        if key_part not in value:
            return None
        value = value[key_part]
    return value


def assign(new_config: Box, force: bool = False) -> None:
    """Set the overall application config.

    This methods sets the global configuration to the given Box object. This method is
    only intended to be used in a subprocess context where reconstructing the
    configuration using ``load`` would be inadvisable.

    Args:
        new_config: The configuration object to be applied
        force: If True, set the config even if one is already set

    Returns:
        None

    Raises:
        ConfigurationError: A config is already loaded and ``force`` is False
    """
    global _CONFIG
    if _CONFIG is not None and not force:
        raise ConfigurationError("Attempting to reset config without force flag")

    _CONFIG = new_config


def _setup_config_sources(spec: YapconfSpec, cli_vars: Iterable[str]) -> List[str]:
    """Sets the sources for configuration loading

    Args:
        spec: Yapconf specification
        cli_vars: Command line arguments

    Returns:
        List of configuration sources
    """
    spec.add_source("cli_args", "dict", data=cli_vars)
    spec.add_source("ENVIRONMENT", "environment")

    config_sources = ["cli_args", "ENVIRONMENT"]

    # Load bootstrap items to see if there's a config file
    temp_config = spec.load_config(*config_sources, bootstrap=True)
    config_filename = temp_config.configuration.file

    if config_filename:
        _safe_migrate(spec, config_filename)
        spec.add_source(config_filename, "yaml", filename=config_filename)
        config_sources.insert(1, config_filename)

    return config_sources


def _safe_migrate(spec: YapconfSpec, filename: str) -> None:
    """Copy existing file to backup before migrating configuration

    Args:
        spec: Yapconf specification
        filename: Config filename

    Returns:
        None
    """
    tmp_filename = filename + ".tmp"
    try:
        spec.migrate_config_file(
            filename,
            current_file_type="yaml",
            output_file_name=tmp_filename,
            output_file_type="yaml",
            include_bootstrap=False,
        )
    except Exception:
        import logging

        # Logging isn't configured yet so this will use the last-chance logger, STDERR
        logging.getLogger(__name__).warning(
            "Could not successfully migrate application configuration. "
            "Will attempt to load the previous configuration.",
            exc_info=True,
        )
        return

    if _is_new_config(filename, tmp_filename):
        _backup_previous_config(filename, tmp_filename)
    else:
        os.remove(tmp_filename)


def _is_new_config(filename, tmp_filename):
    with open(filename, "r") as old_file, open(tmp_filename, "r") as new_file:
        yaml = YAML()
        old_config = yaml.load(old_file)
        new_config = yaml.load(new_file)
    return old_config != new_config


def _backup_previous_config(filename, tmp_filename):
    try:
        os.rename(filename, filename + "_" + datetime.utcnow().isoformat())
    except Exception:
        sys.stderr.write(
            "Could not backup the old configuration. Cowardly refusing to "
            "overwrite the current configuration with the old configuration. "
            "This could cause problems later. Please see %s for the new "
            "configuration file" % tmp_filename
        )
        return

    try:
        os.rename(tmp_filename, filename)
    except Exception:
        sys.stderr.write(
            "ERROR: Config migration was a success, but we could not move the "
            "new config into the old config value. Maybe a permission issue? "
            "Beer Garden cannot start now. To resolve this, you need to rename "
            "%s to %s" % (tmp_filename, filename)
        )
        raise


def _parse_args(args: Sequence[str]) -> Tuple[YapconfSpec, dict]:
    """Construct a spec and parse command line arguments

    Args:
        args: Command line arguments

    Returns:
        Config object with only the named items
    """
    spec = YapconfSpec(_SPECIFICATION, env_prefix="BG_")

    parser = ArgumentParser()
    spec.add_arguments(parser)
    cli_vars = vars(parser.parse_args(args))

    return spec, cli_vars


_GARDEN_SPEC = {
    "type": "dict",
    "items": {
        "name": {
            "type": "str",
            "required": True,
            "default": "default",
            "description": "The routing name for upstream Beer Gardens to use",
        }
    },
}

_META_SPEC = {
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
        }
    },
}

_MQ_SSL_SPEC = {
    "type": "dict",
    "items": {
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
}

_MQ_SPEC = {
    "type": "dict",
    "previous_names": ["amq"],
    "items": {
        "host": {
            "type": "str",
            "default": "localhost",
            "description": (
                "Will be used by the Beergarden application as the location "
                "of the message broker."
            ),
        },
        "admin_queue_expiry": {
            "type": "int",
            "default": 3600000,  # One hour
            "description": "Time before unused admin queues are removed",
        },
        "heartbeat_interval": {
            "type": "int",
            "default": 3600,
            "description": "Heartbeat interval for MQ",
            "previous_names": ["amq_heartbeat_interval"],
        },
        "blocked_connection_timeout": {
            "type": "int",
            "default": 5,
            "description": "Time to wait for a blocked connection to be unblocked",
        },
        "connection_attempts": {
            "type": "int",
            "default": 3,
            "description": "Number of retries to connect to MQ",
            "previous_names": ["amq_connection_attempts"],
        },
        "exchange": {
            "type": "str",
            "default": "beer_garden",
            "description": "Exchange name to use for MQ",
            "previous_names": ["amq_exchange"],
        },
        "virtual_host": {
            "type": "str",
            "default": "/",
            "description": "Virtual host to use for MQ",
            "previous_names": ["amq_virtual_host"],
        },
        "connections": {
            "type": "dict",
            "items": {
                "admin": {
                    "type": "dict",
                    "items": {
                        "port": {
                            "type": "int",
                            "default": 15672,
                            "description": "Port of the MQ Admin host",
                            "previous_names": ["amq_admin_port"],
                            "alt_env_names": ["AMQ_ADMIN_PORT"],
                        },
                        "user": {
                            "type": "str",
                            "default": "guest",
                            "description": "Username to login to the MQ admin",
                            "previous_names": ["amq_admin_user"],
                            "alt_env_names": ["AMQ_ADMIN_USER"],
                        },
                        "password": {
                            "type": "str",
                            "default": "guest",
                            "description": "Password to login to the MQ admin",
                            "previous_names": ["amq_admin_password", "amq_admin_pw"],
                            "alt_env_names": ["AMQ_ADMIN_PASSWORD", "AMQ_ADMIN_PW"],
                        },
                        "ssl": _MQ_SSL_SPEC,
                    },
                },
                "message": {
                    "type": "dict",
                    "items": {
                        "port": {
                            "type": "int",
                            "default": 5672,
                            "description": "Port of the MQ host",
                            "previous_names": ["amq_port"],
                            "alt_env_names": ["AMQ_PORT"],
                        },
                        "password": {
                            "type": "str",
                            "default": "guest",
                            "description": "Password to login to the MQ host",
                            "previous_names": ["amq_password"],
                            "alt_env_names": ["AMQ_PASSWORD"],
                        },
                        "user": {
                            "type": "str",
                            "default": "guest",
                            "description": "Username to login to the MQ host",
                            "previous_names": ["amq_user"],
                            "alt_env_names": ["AMQ_USER"],
                        },
                        "ssl": _MQ_SSL_SPEC,
                    },
                },
            },
        },
    },
}

_UI_SPEC = {
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
        "execute_javascript": {
            "type": "bool",
            "default": False,
            "description": "Execute plugin-provided javascript",
            "long_description": (
                "This is dangerous!! Setting this to true will instruct the browser to"
                " execute javascript provided by plugins. This means you MUST have"
                " control over all plugins running in the environment, otherwise this"
                " is a problem waiting to happen."
            ),
            "previous_names": [
                "application_allow_unsafe_templates",
                "allow_unsanitized_templates",
                "allow_unsafe_templates",
            ],
            "alt_env_names": [
                "APPLICATION_ALLOW_UNSAFE_TEMPLATES",
                "ALLOW_UNSANITIZED_TEMPLATES",
                "BG_ALLOW_UNSAFE_TEMPLATES",
            ],
        },
        "icon_default": {
            "type": "str",
            "description": "Default font-awesome icon to display",
            "default": "fa-beer",
            "previous_names": ["icon_default"],
            "alt_env_names": ["ICON_DEFAULT"],
        },
        "name": {
            "type": "str",
            "default": "Beer Garden",
            "description": "The title to display on the GUI",
            "previous_names": ["application_name"],
        },
    },
}

_AUTHENTICATION_HANDLERS_SPEC = {
    "type": "dict",
    "items": {
        "basic": {
            "type": "dict",
            "items": {
                "enabled": {
                    "type": "bool",
                    "default": True,
                    "description": "Enable authentication via username and" "password",
                }
            },
        },
        "trusted_header": {
            "type": "dict",
            "items": {
                "enabled": {
                    "type": "bool",
                    "default": False,
                    "description": "Enable authentication via trusted headers",
                },
                "username_header": {
                    "type": "str",
                    "default": "bg-username",
                    "description": "The http header containing the username",
                },
                "user_groups_header": {
                    "type": "str",
                    "default": "bg-user-groups",
                    "description": "The http header containing the comma separated "
                    "list of the user's groups.",
                },
                "create_users": {
                    "type": "bool",
                    "default": True,
                    "description": "Create an account for the user specified by"
                    "username_header if one does not already exist",
                },
            },
        },
    },
}


_DEFAULT_ADMIN_SPEC = {
    "type": "dict",
    "items": {
        "username": {
            "type": "str",
            "default": "admin",
            "description": "The username for the default admin account that will "
            "be created when initializing a new environment",
        },
        "password": {
            "type": "str",
            "default": "password",
            "description": "The password for the default admin account that will "
            "be created when initializing a new environment",
        },
    },
}

_AUTH_SPEC = {
    "type": "dict",
    "items": {
        "enabled": {
            "type": "bool",
            "default": False,
            "description": "Use role-based authentication / authorization",
        },
        "default_admin": _DEFAULT_ADMIN_SPEC,
        "token_secret": {
            "type": "str",
            "required": False,
            "description": "Secret to use when signing authentication tokens",
            "default": "",
        },
        "role_definition_file": {
            "type": "str",
            "description": (
                "Path to the yaml file that defines roles used for authorization"
            ),
            "required": False,
        },
        "group_definition_file": {
            "type": "str",
            "description": "Path to the file containg a mapping of "
            "groups to beer garden role assignments",
            "required": False,
        },
        "authentication_handlers": _AUTHENTICATION_HANDLERS_SPEC,
    },
}

_DB_SPEC = {
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
        "ttl": {
            "type": "dict",
            "items": {
                "action": {
                    "type": "int",
                    "default": -1,
                    "description": (
                        "Number of minutes to wait before deleting "
                        "ACTION requests (negative number for never)"
                    ),
                    "previous_names": ["action_request_ttl"],
                    "alt_env_names": ["ACTION_REQUEST_TTL"],
                },
                "admin": {
                    "type": "int",
                    "default": -1,
                    "description": (
                        "Number of minutes to wait before deleting "
                        "Admin requests (negative number for never)"
                    ),
                    "previous_names": [],
                    "alt_env_names": [],
                },
                "info": {
                    "type": "int",
                    "default": 15,
                    "description": (
                        "Number of minutes to wait before deleting "
                        "INFO requests (negative number for never)"
                    ),
                    "previous_names": ["info_request_ttl"],
                    "alt_env_names": ["INFO_REQUEST_TTL"],
                },
                "temp": {
                    "type": "int",
                    "default": 15,
                    "description": (
                        "Number of minutes to wait before deleting "
                        "TEMP requests (negative number for never)"
                    ),
                    "previous_names": [],
                    "alt_env_names": [],
                },
                "in_progress": {
                    "type": "int",
                    "default": -1,
                    "description": (
                        "Number of minutes to wait for a request in CREATED or IN_PROGRESS"
                        "to complete before considering timed out and marking as CANCELLED"
                        "(negative number for never)"
                    ),
                },
                "file": {
                    "type": "int",
                    "default": 15,
                    "description": (
                        "Number of minutes to wait before deleting "
                        "FILE documents (negative number for never)"
                    ),
                    "alt_env_names": ["FILE_REQUEST_TTL"],
                },
                "batch_size": {
                    "type": "int",
                    "default": -1,
                    "description": (
                        "Batch size for deleting documents "
                        "(negative number for never)"
                    ),
                    "alt_env_names": [],
                },
                "multithread": {
                    "type": "bool",
                    "default": False,
                    "description": ("Runs pruners in seperate threads"),
                    "alt_env_names": [],
                },
            },
        },
    },
}

_HTTP_SPEC = {
    "type": "dict",
    "items": {
        "enabled": {
            "type": "bool",
            "default": True,
            "description": "Run an HTTP server",
            "previous_names": ["entry_http_enable"],
        },
        "host": {
            "type": "str",
            "default": "0.0.0.0",
            "description": "Host for the HTTP Server to bind to",
        },
        "port": {
            "type": "int",
            "default": 2337,
            "description": "Serve content on this port",
            "previous_names": ["web_port"],
        },
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
        "url_prefix": {
            "type": "str",
            "default": "/",
            "description": "URL path prefix",
            "required": False,
            "previous_names": ["url_prefix"],
            "alt_env_names": ["URL_PREFIX"],
        },
    },
}

_STOMP_SPEC = {
    "type": "dict",
    "items": {
        "enabled": {
            "type": "bool",
            "default": False,
            "description": "Connect to a Stomp Broker",
        },
        "send_destination": {
            "type": "str",
            "description": "Topic where events are published",
            "required": False,
        },
        "subscribe_destination": {
            "type": "str",
            "description": "Topic to listen for operations",
            "required": False,
        },
        "host": {
            "type": "str",
            "default": "localhost",
            "description": "Broker hostname",
        },
        "port": {
            "type": "int",
            "default": 61613,
            "description": "Broker port",
        },
        "username": {
            "type": "str",
            "description": "Username to use for authentication",
            "required": False,
        },
        "password": {
            "type": "str",
            "description": "Password to use for authentication",
            "required": False,
        },
        "headers": {
            "type": "list",
            "description": (
                "Headers to be sent with messages. Follows standard YAML "
                "formatting for lists with two variables 'key' and 'value'"
            ),
            "required": False,
            "items": {
                "key": {"type": "str"},
                "value": {"type": "str"},
            },
            "default": [],
        },
        "ssl": {
            "type": "dict",
            "items": {
                "use_ssl": {
                    "type": "bool",
                    "description": "Use SSL when connecting to the message broker",
                    "default": False,
                },
                "client_key": {
                    "type": "str",
                    "description": (
                        "Path to client private key to use when "
                        "communicating with the message broker"
                    ),
                    "required": False,
                    "previous_names": ["private_key"],
                },
                "client_cert": {
                    "type": "str",
                    "description": (
                        "Path to client public certificate to use when "
                        "communicating with the message broker"
                    ),
                    "required": False,
                    "previous_names": ["cert_file"],
                },
                "ca_cert": {
                    "type": "str",
                    "description": (
                        "Path to certificate file containing the "
                        "certificate of the authority that issued the "
                        "message broker certificate"
                    ),
                    "required": False,
                },
            },
        },
    },
}

_ENTRY_SPEC = {
    "type": "dict",
    "items": {
        "http": _HTTP_SPEC,
        "stomp": _STOMP_SPEC,
    },
}

_PARENT_SPEC = {
    "type": "dict",
    "items": {
        "http": {
            "type": "dict",
            "items": {
                "enabled": {
                    "type": "bool",
                    "default": False,
                    "description": "Publish events to parent garden over HTTP",
                },
                "host": {
                    "type": "str",
                    "description": "Host for the HTTP Server to bind to",
                    "required": False,
                },
                "port": {
                    "type": "int",
                    "default": 2337,
                    "description": "Serve content on this port",
                },
                "api_version": {
                    "type": "int",
                    "description": "Beergarden API version",
                    "default": 1,
                    "choices": [1],
                },
                "client_timeout": {
                    "type": "float",
                    "description": "Max time RestClient will wait for server response",
                    "long_description": (
                        "This setting controls how long the HTTP(s) client will wait"
                        " when opening a connection to Beergarden before aborting. This"
                        " prevents some strange Beergarden server state from causing"
                        " plugins to hang indefinitely. Set to -1 to disable (this is a"
                        " bad idea in production code, see the Requests documentation)."
                    ),
                    "default": -1,
                },
                "username": {
                    "type": "str",
                    "description": "Username for authentication",
                    "required": False,
                },
                "password": {
                    "type": "str",
                    "description": "Password for authentication",
                    "required": False,
                },
                "access_token": {
                    "type": "str",
                    "description": "Access token for authentication",
                    "required": False,
                },
                "refresh_token": {
                    "type": "str",
                    "description": "Refresh token for authentication",
                    "required": False,
                },
                "ssl": {
                    "type": "dict",
                    "items": {
                        "enabled": {
                            "type": "bool",
                            "default": False,
                            "description": "Use SSL when connecting",
                        },
                        "ca_cert": {
                            "type": "str",
                            "description": (
                                "Path to CA certificate file to use for SSLContext"
                            ),
                            "required": False,
                        },
                        "ca_verify": {
                            "type": "bool",
                            "description": "Verify server certificate when using SSL",
                            "default": True,
                        },
                        "client_cert": {
                            "type": "str",
                            "description": "Client certificate to use",
                            "required": False,
                        },
                        "client_key": {
                            "type": "str",
                            "description": "Client key to use",
                            "required": False,
                        },
                    },
                },
                "url_prefix": {
                    "type": "str",
                    "default": "/",
                    "description": "URL path prefix",
                    "required": False,
                },
            },
        },
        "skip_events": {
            "type": "list",
            "items": {"skip_event": {"type": "str"}},
            "default": [],
            "required": False,
            "description": "Events to be skipped",
        },
        "stomp": {
            "type": "dict",
            "items": {
                "enabled": {
                    "type": "bool",
                    "default": False,
                    "description": "Publish events to parent garden over STOMP",
                },
                "host": {
                    "type": "str",
                    "default": "localhost",
                    "description": "Broker hostname",
                },
                "port": {
                    "type": "int",
                    "default": 61613,
                    "description": "Broker port",
                },
                "username": {
                    "type": "str",
                    "description": "Username to use for authentication",
                    "required": False,
                },
                "password": {
                    "type": "str",
                    "description": "Password to use for authentication",
                    "required": False,
                },
                "send_destination": {
                    "type": "str",
                    "description": "Topic where events are published",
                    "required": False,
                },
                "subscribe_destination": {
                    "type": "str",
                    "description": "Topic to listen for operations",
                    "required": False,
                },
                "headers": {
                    "type": "list",
                    "description": (
                        "Headers to be sent with messages. "
                        "Follows standard YAML formatting for lists with "
                        "two variables 'key' and 'value'"
                    ),
                    "required": False,
                    "items": {
                        "key": {"type": "str"},
                        "value": {"type": "str"},
                    },
                    "default": [],
                },
                "ssl": {
                    "type": "dict",
                    "items": {
                        "use_ssl": {
                            "type": "bool",
                            "description": "Use SSL when connecting to message broker",
                            "default": False,
                        },
                        "client_key": {
                            "type": "str",
                            "description": (
                                "Path to client private key to use when "
                                "communicating with the message broker"
                            ),
                            "required": False,
                            "previous_names": ["private_key"],
                        },
                        "client_cert": {
                            "type": "str",
                            "description": (
                                "Path to client public certificate to use "
                                "when communicating with the message broker"
                            ),
                            "required": False,
                            "previous_names": ["cert_file"],
                        },
                        "ca_cert": {
                            "type": "str",
                            "description": (
                                "Path to certificate file containing the "
                                "certificate of the authority that issued the message "
                                "broker certificate"
                            ),
                            "required": False,
                        },
                    },
                },
            },
        },
    },
}

_LOG_SPEC = {
    "type": "dict",
    "items": {
        "config_file": {
            "type": "str",
            "description": "Path to a logging config file.",
            "required": False,
            "cli_short_name": "l",
            "previous_names": ["log_config"],
            "alt_env_names": ["LOG_CONFIG"],
        },
        "fallback_file": {
            "type": "str",
            "description": "File to log to if config_file is not specified",
            "required": False,
            "previous_names": ["log_file"],
        },
        "fallback_level": {
            "type": "str",
            "description": "Log level to use if config_file is not specified",
            "default": "INFO",
            "choices": ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"],
            "previous_names": ["log_level"],
        },
    },
}

_METRICS_SPEC = {
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
}

_PLUGIN_SPEC = {
    "type": "dict",
    "items": {
        "local": {
            "type": "dict",
            "items": {
                "auth": {
                    "type": "dict",
                    "items": {
                        "username": {
                            "type": "str",
                            "default": "plugin_admin",
                            "description": (
                                "Username that local plugins will use for "
                                "authentication (needs bg-plugin role)"
                            ),
                            "required": False,
                        },
                        "password": {
                            "type": "str",
                            "default": "password",
                            "description": (
                                "Password that local plugins will use for "
                                "authentication (needs bg-plugin role)"
                            ),
                            "required": False,
                        },
                    },
                },
                "directory": {
                    "type": "str",
                    "description": "Directory where local plugins are located",
                    "required": False,
                    "previous_names": ["plugins_directory", "plugin_directory"],
                    "alt_env_names": ["PLUGINS_DIRECTORY", "BG_PLUGIN_DIRECTORY"],
                },
                "host_env_vars": {
                    "type": "list",
                    "items": {"env_var": {"type": "str"}},
                    "default": [],
                    "description": (
                        "Host environment variables that will be propagated "
                        "to local plugin processes"
                    ),
                },
                "logging": {
                    "type": "dict",
                    "items": {
                        "config_file": {
                            "type": "str",
                            "description": (
                                "Path to a logging configuration file for local plugins"
                            ),
                            "required": False,
                        },
                        "fallback_level": {
                            "type": "str",
                            "description": (
                                "Level that will be used with a default logging "
                                "configuration if config_file is not specified"
                            ),
                            "previous_names": ["plugin_logging_level"],
                            "default": "INFO",
                            "choices": [
                                "DEBUG",
                                "INFO",
                                "WARN",
                                "WARNING",
                                "ERROR",
                                "CRITICAL",
                            ],
                        },
                    },
                },
                "timeout": {
                    "type": "dict",
                    "items": {
                        "shutdown": {
                            "type": "int",
                            "default": 10,
                            "description": (
                                "Seconds to wait for a plugin to stopgracefully"
                            ),
                            "previous_names": ["plugin_shutdown_timeout"],
                            "alt_env_names": ["PLUGIN_SHUTDOWN_TIMEOUT"],
                        },
                        "startup": {
                            "type": "int",
                            "default": 5,
                            "description": "Seconds to wait for a plugin to start",
                            "previous_names": ["plugin_startup_timeout"],
                            "alt_env_names": ["PLUGIN_STARTUP_TIMEOUT"],
                        },
                    },
                },
            },
        },
        "mq": {
            "type": "dict",
            "items": {
                "host": {
                    "type": "str",
                    "description": "Globally resolvable host name of message broker",
                    "long_description": (
                        "This will be supplied to all plugins as the location of the"
                        " message broker. In order to support both local and remote"
                        " plugins it's important that this value be universally"
                        " resolvable."
                    ),
                    "default": "localhost",
                    "alt_env_names": ["BG_PUBLISH_HOSTNAME", "PUBLISH_HOSTNAME"],
                },
            },
        },
        "remote": {
            "type": "dict",
            "items": {
                "logging": {
                    "type": "dict",
                    "items": {
                        "config_file": {
                            "type": "str",
                            "description": (
                                "Path to a logging configuration file for plugins"
                            ),
                            "required": False,
                        },
                        "fallback_level": {
                            "type": "str",
                            "description": (
                                "Level that will be used with a default logging "
                                "configuration if config_file is not specified"
                            ),
                            "previous_names": ["plugin_logging_level"],
                            "default": "INFO",
                            "choices": [
                                "DEBUG",
                                "INFO",
                                "WARN",
                                "WARNING",
                                "ERROR",
                                "CRITICAL",
                            ],
                        },
                    },
                },
            },
        },
        "allow_command_updates": {
            "type": "bool",
            "default": False,
            "description": "Allow commands of non-dev systems to be updated",
            "long_description": (
                "When False, this prevents changes to the command definitions of a"
                " registered version of a system. This means that the system will fail"
                " to start if the commands do not match what is on record for that"
                " version of the system. When True, the system will be allowed to start"
                " and the commands on record will be updated accordingly. NOTE: System"
                " versions containing 'dev' are exempt from this check."
            ),
        },
        "status_heartbeat": {
            "type": "int",
            "default": 10,
            "description": "Amount of time between status messages",
            "previous_names": ["plugin_status_heartbeat"],
        },
        "status_timeout": {
            "type": "int",
            "default": 30,
            "description": (
                "Amount of time to wait before marking a plugin asunresponsive"
            ),
            "previous_names": ["plugin_status_timeout "],
        },
    },
}

_SCHEDULER_SPEC = {
    "type": "dict",
    "items": {
        "max_workers": {
            "type": "int",
            "default": 10,
            "description": "Number of workers (processes) to run concurrently.",
        },
        "job_defaults": {
            "type": "dict",
            "items": {
                "coalesce": {
                    "type": "bool",
                    "default": True,
                    "description": (
                        "Should jobs run only once if multiple have missed their window"
                    ),
                },
                "max_instances": {
                    "type": "int",
                    "default": 3,
                    "description": (
                        "Default maximum instances of a job to run concurrently."
                    ),
                },
            },
        },
    },
}

_REQUEST_VALIDATION_SPEC = {
    "type": "dict",
    "items": {
        "dynamic_choices": {
            "type": "dict",
            "items": {
                "command": {
                    "type": "dict",
                    "items": {
                        "timeout": {
                            "type": "int",
                            "default": 10,
                            "description": (
                                "Time to wait for a command-based choices validation"
                            ),
                            "required": False,
                        }
                    },
                },
                "url": {
                    "type": "dict",
                    "items": {
                        "ca_cert": {
                            "type": "str",
                            "description": "CA file for validating url-based choices",
                            "required": False,
                        },
                        "ca_verify": {
                            "type": "bool",
                            "default": True,
                            "description": (
                                "Verify external certificates for url-based choices"
                            ),
                            "required": False,
                        },
                    },
                },
            },
        },
    },
}

_SPECIFICATION = {
    "auth": _AUTH_SPEC,
    "configuration": _META_SPEC,
    "db": _DB_SPEC,
    "entry": _ENTRY_SPEC,
    "garden": _GARDEN_SPEC,
    "log": _LOG_SPEC,
    "metrics": _METRICS_SPEC,
    "mq": _MQ_SPEC,
    "parent": _PARENT_SPEC,
    "plugin": _PLUGIN_SPEC,
    "request_validation": _REQUEST_VALIDATION_SPEC,
    "scheduler": _SCHEDULER_SPEC,
    "ui": _UI_SPEC,
}
