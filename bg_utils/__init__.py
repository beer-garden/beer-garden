import datetime
import json
import logging
import logging.config
import os
from argparse import ArgumentParser
from io import open

import six
import sys
import thriftpy
import yapconf

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
    config_file, config_type = _get_config_values(config)

    yapconf.dump_data(config.to_dict(), filename=config_file,
                      file_type=config_type)


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
    config_file, config_type = _get_config_values(config)

    if not config_file:
        raise SystemExit('Please specify a config file to update'
                         ' in the CLI arguments (-c)')

    spec.migrate_config_file(config_file, update_defaults=True,
                             current_file_type=config_type,
                             output_file_type=config_type)


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
            dumped = json.dumps(logging_config, indent=4, sort_keys=True)
            f.write(six.u(dumped))
    else:
        print(json.dumps(logging_config, indent=4, sort_keys=True))

    return logging_config


def load_application_config(spec, cli_args):

    spec.add_source('cli_args', 'dict', data=cli_args)
    spec.add_source('ENVIRONMENT', 'environment')

    config_sources = ['cli_args', 'ENVIRONMENT']

    # Load bootstrap items to see if there's a config file
    temp_config = spec.load_config(*config_sources, bootstrap=True)

    if temp_config.configuration.file:
        if temp_config.configuration.type:
            file_type = temp_config.configuration.type
        elif temp_config.configuration.file.endswith('json'):
            file_type = 'json'
        else:
            file_type = 'yaml'
        filename = temp_config.configuration.file
        _safe_migrate(spec, filename, file_type)
        spec.add_source(filename, 'yaml', filename=filename)
        config_sources.insert(1, filename)

    return spec.load_config(*config_sources)


def _safe_migrate(spec, filename, file_type):
    tmp_filename = filename + '.tmp'
    try:
        spec.migrate_config_file(
            filename,
            current_file_type=file_type,
            output_file_name=tmp_filename,
            output_file_type='yaml',
        )
    except Exception:
        sys.stderr.write(
            'Could not successfully migrate application configuration.'
            'will attempt to load the previous configuration.'
        )
        return
    if _is_new_config(spec, filename, file_type, tmp_filename):
        _swap_files(filename, tmp_filename)
    else:
        os.remove(tmp_filename)


def _is_new_config(spec, filename, file_type, tmp_filename):
    old_config = spec.load_config(('old_config', filename, file_type))
    new_config = spec.load_config(('new_config', tmp_filename, 'yaml'))
    return old_config != new_config or file_type != 'yaml'


def _swap_files(filename, tmp_filename):
    try:
        os.rename(filename, filename + '_' + datetime.datetime.utcnow().isoformat())
    except Exception:
        sys.stderr.write(
            'Could not backup the old configuration. Cowardly refusing to overwrite '
            'the current configuration with the old configuration. This could cause '
            'problems later. Please see %s for the new configuration file' % tmp_filename
        )
        return

    try:
        os.rename(tmp_filename, filename)
    except Exception:
        sys.stderr.write(
            'ERROR: Config migration was a success, but we could not move the '
            'new config into the old config value. Maybe a permission issue? '
            'Beer Garden cannot start now. To resolve this, you need to rename '
            '%s to %s' % (tmp_filename, filename)
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
        with open(config.log.config_file, 'rt') as f:
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
    from mongoengine import connect, register_connection
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

    try:
        # Set timeouts here to a low value - we don't want to wait 30
        # seconds if there's no database
        conn = connect(alias='aliveness', db=config.db.name,
                       socketTimeoutMS=1000, serverSelectionTimeoutMS=1000,
                       **config.db.connection)

        # The 'connect' method won't actually fail
        # An exception won't be raised until we actually try to do something
        conn.server_info()

        # Close the aliveness connection - the timeouts are too low
        conn.close()
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False

    # Now register the default connection with real timeouts
    # Yes, mongoengine uses 'db' in connect and 'name' in register_connection
    register_connection('default', name=config.db.name, **config.db.connection)

    _verify_db()

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


def _get_config_values(config):
    """Get the configuration file name and type from a configuration"""

    config_file = config.configuration.file or None
    config_type = config.configuration.type or None

    # Default to yaml, but try to use file extension if we have one
    if config_type is None:
        if config_file and config_file.endswith('json'):
            config_type = 'json'
        else:
            config_type = 'yaml'

    return config_file, config_type


def _verify_db():
    """Ensures indexes are correct and attempts to rebuild ALL OF THEM if any aren't
    (blame MongoEngine). If anything goes wrong with the rebuild kill the app since the database
    is in a bad state.
    """

    from .models import Request, System
    logger = logging.getLogger(__name__)

    def update_request_model():
        raw_collection = Request._get_collection()
        raw_collection.update_many({'parent':  None},
                                   {'$set': {'has_parent': False}})
        raw_collection.update_many({'parent': {'$not': {'$eq': None}}},
                                   {'$set': {'has_parent': True}},)

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
                logger.warning('Found missing %s indexes, about to build them. '
                               'This could take a while :)',
                               collection.__name__)

            collection.ensure_indexes()

        except OperationFailure:
            logger.warning('%s collection indexes verification failed, '
                           'attempting to rebuild', collection.__name__)

            # Unfortunately mongoengine sucks. The index that failed is only returned as part of
            # the error message. I REALLY don't want to parse an error string to find the index to
            # drop. Also, ME only verifies / creates the indexes in bulk - there's no way to
            # iterate through the index definitions and try them one by one. Since our indexes
            # should be small and built in the background anyway we're just gonna redo all of them

            try:
                db = get_db()
                db[collection.__name__.lower()].drop_indexes()
                logger.warning('Dropped indexes for %s collection', collection.__name__)
            except OperationFailure:
                logger.error('Dropping %s indexes failed, please check the database configuration',
                             collection.__name__)
                raise

            # For bg-utils 2.3.3 -> 2.3.4 upgrade
            # We need to create the `has_parent` field
            if collection == Request:
                logger.warning('Request definition is out of date, updating')
                update_request_model()

            try:
                collection.ensure_indexes()
                logger.warning('%s indexes rebuilt successfully', collection.__name__)
            except OperationFailure:
                logger.error('%s index rebuild failed, please check the database configuration',
                             collection.__name__)
                raise

    check_indexes(Request)
    check_indexes(System)
