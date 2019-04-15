import json
import logging
import logging.config
import os
import sys
from argparse import ArgumentParser
from datetime import datetime
from io import open

import six
import thriftpy2
import yapconf
from ruamel.yaml import YAML

from ._version import __version__ as generated_version

__version__ = generated_version

logger = logging.getLogger(__name__)

bg_thrift = thriftpy2.load(
    os.path.join(os.path.dirname(__file__), "thrift", "beergarden.thrift"),
    include_dirs=[os.path.join(os.path.dirname(__file__), "thrift")],
    module_name="bg_thrift",
)


def parse_args(spec, item_names, cli_args):
    """Parse command-line arguments for specific item names

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        item_names(List[str]): Names to parse
        cli_args (List[str]): Command line arguments

    Returns:
        dict: Argument values
    """

    def find_item(spec, item_name):
        name_parts = item_name.split(spec._separator)
        base_name = name_parts[0]
        to_return = spec.get_item(base_name)
        for name in name_parts[1:]:
            to_return = to_return.children[name]
        return to_return

    parser = ArgumentParser()
    for item_name in item_names:
        item = find_item(spec, item_name)
        item.add_argument(parser)

    args = vars(parser.parse_args(cli_args))
    for item_name in item_names:
        name_parts = item_name.split(spec._separator)
        if len(name_parts) <= 1:
            if args[name_parts[0]] is None:
                args[name_parts[0]] = find_item(spec, item_name).default
            continue

        current_arg_value = args.get(name_parts[0], {})
        default_value = {}
        item = spec.get_item(name_parts[0])
        for name in name_parts[1:]:
            default_value[name] = {}
            item = item.children[name]
            current_arg_value = current_arg_value.get(name, {})
        default_value[name_parts[-1]] = item.default
        if not current_arg_value:
            if not args.get(name_parts[0]):
                args[name_parts[0]] = {}
            args[name_parts[0]].update(default_value)

    return args


def generate_config_file(spec, cli_args):
    """Generate a configuration file.

    Takes a specification and a series of command line arguments. Will create a
    file at the location specified by the resolved `config` value. If none
    exists the configuration will be printed to stdout.

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        cli_args (List[str]): Command line arguments

    Returns:
        None

    Raises:
        YapconfLoadError: Missing 'config' configuration option (file location)
    """
    config = _generate_config(spec, cli_args)

    # Bootstrap items shouldn't be in the generated config file
    # We mimic a migration as it's the easiest way to filter out bootstrap items
    items = [item for item in spec._yapconf_items.values() if not item.bootstrap]
    filtered_config = {}
    for item in items:
        item.migrate_config(
            config, filtered_config, always_update=False, update_defaults=False
        )

    yapconf.dump_data(
        filtered_config,
        filename=config.configuration.file,
        file_type=_get_config_type(config),
    )


def update_config_file(spec, cli_args):
    """Updates a configuration file in-place.

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        cli_args (List[str]): Command line arguments. Must contain an argument
            that specifies the config file to update ('-c')
    Returns:
        None

    Raises:
        YapconfLoadError: Missing 'config' configuration option (file location)
    """
    config = _generate_config(spec, cli_args)

    if not config.configuration.file:
        raise SystemExit(
            "Please specify a config file to update" " in the CLI arguments (-c)"
        )

    current_root, current_extension = os.path.splitext(config.configuration.file)

    current_type = current_extension[1:]
    if current_type == "yml":
        current_type = "yaml"

    # Determine if a type conversion is needed
    type_conversion = False
    new_type = _get_config_type(config)
    if current_type != new_type:
        new_file = current_root + "." + new_type
        type_conversion = True
    else:
        new_file = config.configuration.file

    logger.debug("About to migrate config at %s" % config.configuration.file)
    spec.migrate_config_file(
        config.configuration.file,
        current_file_type=current_type,
        output_file_name=new_file,
        output_file_type=new_type,
        update_defaults=True,
        include_bootstrap=False,
    )

    if type_conversion:
        logger.debug("Removing old config file at %s" % config.configuration.file)
        os.remove(config.configuration.file)


def generate_logging_config_file(spec, logging_config_generator, cli_args):
    """Generate and save logging configuration file.

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        logging_config_generator (method): Method to generate default logging configuration
            Args:
                level (str): Logging level to use
                filename (str): File to use in RotatingFileHandler configuration
        cli_args (List[str]): Command line arguments
            --log-config-file: Configuration will be written to this file (will print to
                stdout if missing)
            --log-file: Logs will be written to this file (used in a RotatingFileHandler)
            --log-level: Handlers will be configured with this logging level

    Returns:
        str: The logging configuration dictionary
    """
    args = parse_args(spec, ["log.config_file", "log.file", "log.level"], cli_args)

    log = args.get("log", {})
    logging_config = logging_config_generator(log.get("level"), log.get("file"))
    log_config_file = log.get("config_file")

    if log_config_file is not None:
        with open(log_config_file, "w") as f:
            dumped = json.dumps(logging_config, indent=4, sort_keys=True)
            f.write(six.u(dumped))
    else:
        print(json.dumps(logging_config, indent=4, sort_keys=True))

    return logging_config


def load_application_config(spec, cli_args):

    spec.add_source("cli_args", "dict", data=cli_args)
    spec.add_source("ENVIRONMENT", "environment")

    config_sources = ["cli_args", "ENVIRONMENT"]

    # Load bootstrap items to see if there's a config file
    temp_config = spec.load_config(*config_sources, bootstrap=True)

    if temp_config.configuration.file:
        if temp_config.configuration.type:
            file_type = temp_config.configuration.type
        elif temp_config.configuration.file.endswith("json"):
            file_type = "json"
        else:
            file_type = "yaml"
        filename = temp_config.configuration.file
        _safe_migrate(spec, filename, file_type)
        spec.add_source(filename, file_type, filename=filename)
        config_sources.insert(1, filename)

    return spec.load_config(*config_sources)


def _safe_migrate(spec, filename, file_type):
    tmp_filename = filename + ".tmp"
    try:
        spec.migrate_config_file(
            filename,
            current_file_type=file_type,
            output_file_name=tmp_filename,
            output_file_type=file_type,
            include_bootstrap=False,
        )
    except Exception:
        sys.stderr.write(
            "Could not successfully migrate application configuration. "
            "Will attempt to load the previous configuration."
        )
        return
    if _is_new_config(filename, file_type, tmp_filename):
        _swap_files(filename, tmp_filename)
    else:
        os.remove(tmp_filename)


def _is_new_config(filename, file_type, tmp_filename):
    with open(filename, "r") as f, open(tmp_filename, "r") as g:
        if file_type == "json":
            old_config = json.load(f)
            new_config = json.load(g)
        elif file_type == "yaml":
            yaml = YAML()
            old_config = yaml.load(f)
            new_config = yaml.load(g)
        else:
            raise ValueError("Unsupported file type %s" % file_type)

    return old_config != new_config


def _swap_files(filename, tmp_filename):
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


def setup_application_logging(config, default_config):
    """Setup the application logging based on the config object.

    If config.log_config is not set then the default_logging_config will be used.

    Args:
        config (box.Box): The application configuration object
        default_config (dict): Dictionary configuration to use if config.log_config is missing

    Returns:
        dict: The logging configuration used
    """
    if config.log.config_file:
        with open(config.log.config_file, "rt") as f:
            logging_config = json.load(f)
    else:
        logging_config = default_config

    logging.config.dictConfig(logging_config)

    return logging_config


def _generate_config(spec, cli_args):
    """Generate a configuration from a spec and command line arguments.

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        cli_args (List[str]): Command line arguments

    Returns:
        box.Box: The generated configuration object
    """
    parser = ArgumentParser()
    spec.add_arguments(parser)
    args = parser.parse_args(cli_args)

    return spec.load_config(vars(args), "ENVIRONMENT")


def _get_config_type(config):
    """Get configuration type from a configuration"""

    if config.configuration.type:
        return config.configuration.type

    if config.configuration.file and config.configuration.file.endswith("json"):
        return "json"

    return "yaml"
