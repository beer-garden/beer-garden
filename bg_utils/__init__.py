import json
import logging
import logging.config
import os
from argparse import ArgumentParser
from io import open

import thriftpy

from ._version import __version__ as generated_version

__version__ = generated_version

bg_thrift = thriftpy.load(os.path.join(os.path.dirname(__file__), 'thrift', 'beergarden.thrift'),
                          include_dirs=[os.path.join(os.path.dirname(__file__), 'thrift')],
                          module_name='bg_thrift')


def parse_args(spec, item_names, cli_args):
    """Parse command-line arguments for specific item names

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        item_names(List[str]): Names to parse
        cli_args (List[str]): Command line arguments

    Returns:
        Namespace: Arguments object
    """
    parser = ArgumentParser()
    for item_name in item_names:
        item = spec.get_item(item_name)
        item.add_argument(parser)

    args = parser.parse_args(cli_args)
    for item_name in item_names:
        if getattr(args, item_name) is None:
            item = spec.get_item(item_name)
            setattr(args, item_name, item.default)

    return args


def generate_config_file(spec, cli_args):
    """Generate a configuration file.

    Takes a specification and a series of command line arguments. Will create a file at the
    location specified by the resolved `config` value. If none exists the configuration will
    be printed to stdout.

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        cli_args (List[str]): Command line arguments

    Returns:
        None

    Raises:
        YapconfLoadError: Missing 'config' configuration option (file location)
    """
    config = _generate_config(spec, cli_args)

    if config.get('config', None):
        spec._write_dict_to_file(config, config.config, 'json')
    else:
        print(config)


def update_config_file(spec, cli_args):
    """Updates a configuration file in-place.

    cli_args must contain a 'config' argument that specifies the config file to update.

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        cli_args (List[str]): Command line arguments

    Returns:
        None

    Raises:
        YapconfLoadError: Missing 'config' configuration option (file location)
    """
    spec.get_item("config").required = True
    config = _generate_config(spec, cli_args)

    spec.migrate_config_file(config.config, update_defaults=True)


def generate_logging_config_file(spec, logging_config_generator, cli_args):
    """Generate and save logging configuration file.

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        logging_config_generator (method): Method to generate default logging configuration
            Args:
                level (str): Logging level to use
                filename (str): File to use in RotatingFileHandler configuration
        cli_args (List[str]): Command line arguments
            --log_config: Configuration will be written to this file (will print to stdout
                if missing)
            --log_file: Logs will be written to this file (used in a RotatingFileHandler)
            --log_level: Handlers will be configured with this logging level

    Returns:
        str: The logging configuration dictionary
    """
    args = parse_args(spec, ["log_config", "log_file", "log_level"], cli_args)

    logging_config = logging_config_generator(args.log_level, args.log_file)

    if args.log_config is not None:
        with open(args.log_config, 'w') as f:
            json.dump(logging_config, f, indent=4, sort_keys=True)
    else:
        print(json.dumps(logging_config, indent=4, sort_keys=True))

    return logging_config


def setup_application_logging(config, default_config):
    """Setup the application logging based on the config object.

    If config.log_config is not set then the default_logging_config will be used.

    Args:
        config (box.Box): The application configuration object
        default_config (dict): Dictionary configuration to use if config.log_config is missing

    Returns:
        dict: The logging configuration used
    """
    if config.log_config:
        with open(config.log_config, 'rt') as f:
            logging_config = json.load(f)
    else:
        logging_config = default_config

    logging.config.dictConfig(logging_config)

    return logging_config


def setup_database(config):
    """Attempt connection to a Mongo database and verify necessary indexes

    Args:
        config (box.Box): Yapconf-generated configuration object

    Returns:
        bool: True if successful, False otherwise (unable to connect)

    Raises:
        Any mongoengine or pymongo error *except* ConnectionFailure, ServerSelectionTimeoutError
    """
    from mongoengine import connect
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

    try:
        connect(db=config.db_name, username=config.db_username,
                password=config.db_password, host=config.db_host,
                port=config.db_port, socketTimeoutMS=1000,
                serverSelectionTimeoutMS=1000)

        # The 'connect' method won't actually fail
        # An exception won't be raised until we actually try to do something
        _verify_db()
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False

    return True


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

    return spec.load_config(vars(args), 'ENVIRONMENT')


def _verify_db():
    """Ensures indexes are correct and attempts to rebuild ALL OF THEM if any aren't
    (blame MongoEngine). If anything goes wrong with the rebuild kill the app since the database
    is in a bad state.
    """

    from .models import Request, System
    logger = logging.getLogger(__name__)

    def check_indexes(collection):
        from pymongo.errors import OperationFailure
        from mongoengine.connection import get_db

        try:
            # Building the indexes could take a while so it'd be nice to give some indication
            # of what's happening. This would be perfect but can't use it! It's broken for text
            # indexes!! MongoEngine is awesome!!
            # index_diff = collection.compare_indexes(); if index_diff['missing'] is not None...

            # Since we can't ACTUALLY compare the index spec with what already exists without
            # ridiculous effort:
            spec = collection.list_indexes()
            existing = collection._get_collection().index_information()

            if len(spec) > len(existing):
                logger.info('Found missing %s indexes, about to build them. '
                            'This could take a while :)',
                            collection.__name__)

            collection.ensure_indexes()

        except OperationFailure:
            logger.warning('%s collection indexes verification failed, attempting to rebuild',
                           collection.__name__)

            # Unfortunately mongoengine sucks. The index that failed is only returned as part of
            # the error message. I REALLY don't want to parse an error string to find the index to
            # drop. Also, ME only verifies / creates the indexes in bulk - there's no way to
            # iterate through the index definitions and try them one by one. Since our indexes
            # should be small and built in the background anyway we're just gonna redo all of them

            try:
                db = get_db()
                db[collection.__name__.lower()].drop_indexes()
                logger.info('Dropped indexes for %s collection', collection.__name__)
            except OperationFailure:
                logger.error('Dropping %s indexes failed, please check the database configuration',
                             collection.__name__)
                raise

            try:
                collection.ensure_indexes()
                logger.warning('%s indexes rebuilt successfully', collection.__name__)
            except OperationFailure:
                logger.error('%s index rebuild failed, please check the database configuration',
                             collection.__name__)
                raise

    check_indexes(Request)
    check_indexes(System)
