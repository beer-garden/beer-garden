import json
import logging
import logging.config
import os
from argparse import ArgumentParser
from io import open

import thriftpy

from ._version import __version__ as generated_version
from .fields import DummyField, StatusInfo
from .models import Command, Instance, Parameter, Request, System, Event

__version__ = generated_version

bg_thrift = thriftpy.load(os.path.join(os.path.dirname(__file__), 'thrift', 'beergarden.thrift'),
                          include_dirs=[os.path.join(os.path.dirname(__file__), 'thrift')],
                          module_name='bg_thrift')


def parse_args(config_spec, item_names, cli_args):
    """Parse command-line arguments for specific item names

    :param config_spec: ConfigSpec for your application
    :param item_names: The name of the config items to parse out
    :param cli_args: The command-line arguments
    :return: Namespace args object
    """
    parser = ArgumentParser()
    for item_name in item_names:
        item = config_spec.get_item(item_name)
        item.add_argument(parser)

    args = parser.parse_args(cli_args)
    for item_name in item_names:
        if getattr(args, item_name) is None:
            item = config_spec.get_item(item_name)
            setattr(args, item_name, item.default)
    return args


def generate_logging_config(config_spec, default_config_generator, cli_args):
    """Generate logging configuration file. If no log_config is reported, simply prints out a logging config

    The default_config_generator must accept a log level and filename as arguments

    :param config_spec: ConfigSpec for your application
    :param default_config_generator: method to generate a default logging config
    :param cli_args: Command-line arguments
    :return:
    """
    args = parse_args(config_spec, ["log_config", "log_file", "log_level"], cli_args)

    default_logging_config = default_config_generator(args.log_level, args.log_file)

    config_string = json.dumps(default_logging_config, indent=4, sort_keys=True)
    if args.log_config is None:
        print(config_string)
    else:
        with open(args.log_config, 'w') as f:
            f.write(str(config_string))

    return config_string


def generate_config(config_spec, cli_args):
    """Generate application configuration. If no config is reported, simply print out a config

    :param config_spec: ConfigSpec for your application
    :param cli_args: Command-line arguments
    :return:
    """
    parser = ArgumentParser()
    config_spec.add_arguments_to_parser(parser)
    args = parser.parse_args(cli_args)
    app_config = config_spec.load_app_config(vars(args), 'ENVIRONMENT')
    if app_config.config:
        config_spec.output_config(app_config.info, output_file_path=app_config.config, output_file_type='json')
    else:
        print(config_spec.output_config(app_config.info))


def migrate_config(config_spec, cli_args):
    """Migrate a config file

    Requires the config argument be passed in the cli_args

    :param config_spec: ConfigSpec for your application
    :param cli_args: Command-line arguments
    :return:
    """
    parser = ArgumentParser()
    config_spec.get_item("config").required = True
    config_spec.add_arguments_to_parser(parser)
    args = parser.parse_args(cli_args)
    app_config = config_spec.load_app_config(vars(args), 'ENVIRONMENT')
    config_spec.update_defaults(app_config.info)

    config_spec.migrate_config_file(app_config.config, override_current=False, current_config_file_type="json",
                                    output_file_name=app_config.config, output_file_type="json", create=True,
                                    update_defaults=True)


def setup_application_logging(app_config, default_logging_config):
    """Setup the application logging based on the app_config object.

    If app_config.log_config is not set, then the default_logging_config will be used.

    :param app_config: Return value from config_spec.load_app_config
    :param default_logging_config: A default logging config dictionary
    :return:
    """
    if app_config.log_config:
        with open(app_config.log_config, 'rt') as f:
            logging_config = json.load(f)
    else:
        logging_config = default_logging_config

    logging.config.dictConfig(logging_config)
    return logging_config


def setup_database(app_config):
    from mongoengine import connect
    logger = logging.getLogger(__name__)

    logger.debug("Connecting to database.")
    logger.debug("Name: %s" % app_config.db_name)
    logger.debug("Username: %s" % app_config.db_username)
    logger.debug("Host: %s" % app_config.db_host)
    logger.debug("Port: %s" % app_config.db_port)

    connect(db=app_config.db_name,
            username=app_config.db_username,
            password=app_config.db_password,
            host=app_config.db_host,
            port=app_config.db_port)
    _verify_db()


def _verify_db():
    """Ensures indexes are correct and attempts to rebuild ALL OF THEM if any aren't (blame MongoEngine).
    If anything goes wrong with the rebuild kill the app since the database is in a bad state.
    """

    from .models import Command, Instance, Parameter, Request, System, Event
    logger = logging.getLogger(__name__)

    def check_indexes(collection):
        from pymongo.errors import OperationFailure
        from mongoengine.connection import get_db

        try:
            # Building the indexes could take a while so it'd be nice to give some indication of what's happening.
            # This would be perfect but can't use it! It's broken for text indexes!! MongoEngine is awesome!!
            # index_diff = collection.compare_indexes(); if index_diff['missing'] is not None...

            # Since we can't ACTUALLY compare the index spec with what already exists without ridiculous effort:
            spec = collection.list_indexes()
            existing = collection._get_collection().index_information()

            if len(spec) > len(existing):
                logger.info('Found missing %s indexes, about to build them. This could take a while :)',
                            collection.__name__)

            collection.ensure_indexes()

        except OperationFailure:
            logger.warning('%s collection indexes verification failed, attempting to rebuild', collection.__name__)

            # Unfortunately mongoengine sucks. The index that failed is only returned as part of the error message.
            # I REALLY don't want to parse an error string to find the index to drop. Also, ME only verifies / creates
            # the indexes in bulk - there's no way to iterate through the index definitions and try them one by one.
            # Since our indexes should be small and built in the background anyway we're just gonna redo all of them

            try:
                db = get_db()
                db[collection.__name__.lower()].drop_indexes()
                logger.info('Dropped indexes for %s collection', collection.__name__)
            except OperationFailure:
                logger.error('Dropping %s indexes failed, please check the database configuration', collection.__name__)
                raise

            try:
                collection.ensure_indexes()
                logger.warning('%s indexes rebuilt successfully', collection.__name__)
            except OperationFailure:
                logger.error('%s index rebuild failed, please check the database configuration', collection.__name__)
                raise

    check_indexes(Request)
    check_indexes(System)
