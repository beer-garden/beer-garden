import json
import logging
import logging.config
import os
import sys
from argparse import ArgumentParser
from datetime import datetime
from io import open

import six
import thriftpy
import yapconf
from mongoengine.errors import DoesNotExist
from passlib.apps import custom_app_context
from ruamel.yaml import YAML

from ._version import __version__ as generated_version

__version__ = generated_version

logger = logging.getLogger(__name__)

bg_thrift = thriftpy.load(
    os.path.join(os.path.dirname(__file__), 'thrift', 'beergarden.thrift'),
    include_dirs=[os.path.join(os.path.dirname(__file__), 'thrift')],
    module_name='bg_thrift'
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
            --log-config-file: Configuration will be written to this file (will print to
                stdout if missing)
            --log-file: Logs will be written to this file (used in a RotatingFileHandler)
            --log-level: Handlers will be configured with this logging level

    Returns:
        str: The logging configuration dictionary
    """
    args = parse_args(spec, ["log.config_file", "log.file", "log.level"], cli_args)

    log = args.get('log', {})
    logging_config = logging_config_generator(log.get('level'), log.get('file'))
    log_config_file = log.get('config_file')

    if log_config_file is not None:
        with open(log_config_file, 'w') as f:
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
        spec.add_source(filename, file_type, filename=filename)
        config_sources.insert(1, filename)

    return spec.load_config(*config_sources)


def _safe_migrate(spec, filename, file_type):
    tmp_filename = filename + '.tmp'
    try:
        spec.migrate_config_file(
            filename,
            current_file_type=file_type,
            output_file_name=tmp_filename,
            output_file_type=file_type,
        )
    except Exception:
        sys.stderr.write(
            'Could not successfully migrate application configuration.'
            'will attempt to load the previous configuration.'
        )
        return
    if _is_new_config(filename, file_type, tmp_filename):
        _swap_files(filename, tmp_filename)
    else:
        os.remove(tmp_filename)


def _is_new_config(filename, file_type, tmp_filename):
    with open(filename, 'r') as f, open(tmp_filename, 'r') as g:
        if file_type == 'json':
            old_config = json.load(f)
            new_config = json.load(g)
        elif file_type == 'yaml':
            yaml = YAML()
            old_config = yaml.load(f)
            new_config = yaml.load(g)
        else:
            raise ValueError('Unsupported file type %s' % file_type)

    return old_config != new_config


def _swap_files(filename, tmp_filename):
    try:
        os.rename(filename, filename + '_' + datetime.utcnow().isoformat())
    except Exception:
        sys.stderr.write(
            'Could not backup the old configuration. Cowardly refusing to '
            'overwrite the current configuration with the old configuration. '
            'This could cause problems later. Please see %s for the new '
            'configuration file' % tmp_filename
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


def _update_request_model():
    from .models import Request

    raw_collection = Request._get_collection()
    raw_collection.update_many({'parent':  None},
                               {'$set': {'has_parent': False}})
    raw_collection.update_many({'parent': {'$not': {'$eq': None}}},
                               {'$set': {'has_parent': True}},)


def _ensure_roles():
    """Create roles if necessary

    There are certain 'convenience' roles that will be created if this is a new
    install (if no roles currently exist).

    Then there are roles that MUST be present. These will always be created if
    they do not exist.
    """
    from .models import Role

    if Role.objects.count() == 0:
        logger.warning('No roles found: creating convenience roles')

        logger.warning('About to create bg-readonly role')
        Role(
            name='bg-readonly',
            description='Allows only standard read actions',
            permissions=[
                'bg-command-read',
                'bg-event-read',
                'bg-instance-read',
                'bg-job-read',
                'bg-queue-read',
                'bg-request-read',
                'bg-system-read',
            ]
        ).save()

        logger.warning('About to create bg-operator role')
        Role(
            name='bg-operator',
            description='Standard Beergarden user role',
            roles=[Role.objects.get(name='bg-readonly')],
            permissions=[
                'bg-request-create',
            ]
        ).save()

    try:
        Role.objects.get(name='bg-plugin')
    except DoesNotExist:
        logger.warning('Role bg-plugin missing, about to create')
        Role(
            name='bg-plugin',
            description='Allows actions necessary for plugins to function',
            permissions=[
                'bg-instance-update',
                'bg-job-create',
                'bg-job-update',
                'bg-request-create',
                'bg-request-update',
                'bg-system-create',
                'bg-system-read',
                'bg-system-update',
            ]
        ).save()

    try:
        Role.objects.get(name='bg-admin')
    except DoesNotExist:
        logger.warning('Role bg-admin missing, about to create')
        Role(
            name='bg-admin',
            description='Allows all actions',
            permissions=['bg-all']
        ).save()

    try:
        Role.objects.get(name='bg-anonymous')
    except DoesNotExist:
        logger.warning('Role bg-anonymous missing, about to create')
        Role(
            name='bg-anonymous',
            description='Special role used for non-authenticated users',
            permissions=[
                'bg-command-read',
                'bg-event-read',
                'bg-instance-read',
                'bg-job-read',
                'bg-queue-read',
                'bg-request-read',
                'bg-system-read',
            ]
        ).save()


def _ensure_users():
    """Create users if necessary

    There are certain 'convenience' users that will be created if this is a new
    install (if no users currently exist).

    Then there are users that MUST be present. These will always be created if
    they do not exist.
    """
    from .models import Principal, Role

    if Principal.objects.count() == 0:
        logger.warning('No users found: creating convenience users')

        logger.warning('Creating plugin user '
                       '(username "plugin", password "password"')
        Principal(
            username='plugin',
            hash=custom_app_context.hash('password'),
            roles=[Role.objects.get(name='bg-plugin')]
        ).save()

    try:
        Principal.objects.get(username='admin')
    except DoesNotExist:
        logger.warning('Admin user missing, about to create '
                       '(username "admin", password "password")')
        Principal(
            username='admin',
            hash=custom_app_context.hash('password'),
            roles=[Role.objects.get(name='bg-admin')]
        ).save()

    try:
        Principal.objects.get(username='anonymous')
    except DoesNotExist:
        logger.warning('Anonymous user missing, about to create '
                       '(username "anonymous")')
        Principal(
            username='anonymous',
            roles=[Role.objects.get(name='bg-anonymous')]
        ).save()


def _check_indexes(document_class):
    """Ensures indexes are correct.

    If any indexes are missing they will be created.

    If any of them are 'wrong' (fields have changed, etc.) all the indexes for
    that collection will be dropped and rebuilt.

    Args:
        document_class (Document): The document class

    Returns:
        None

    Raises:
        mongoengine.OperationFailure: Unhandled mongo error
    """
    from pymongo.errors import OperationFailure
    from mongoengine.connection import get_db
    from .models import Request

    try:
        # Building the indexes could take a while so it'd be nice to give some indication
        # of what's happening. This would be perfect but can't use it! It's broken for text
        # indexes!! MongoEngine is awesome!!
        # index_diff = collection.compare_indexes(); if index_diff['missing'] is not None...

        # Since we can't ACTUALLY compare the index spec with what already exists without
        # ridiculous effort:
        spec = document_class.list_indexes()
        existing = document_class._get_collection().index_information()

        if len(spec) > len(existing):
            logger.warning('Found missing %s indexes, about to build them. '
                           'This could take a while :)',
                           document_class.__name__)

        document_class.ensure_indexes()

    except OperationFailure:
        logger.warning('%s collection indexes verification failed, '
                       'attempting to rebuild', document_class.__name__)

        # Unfortunately mongoengine sucks. The index that failed is only returned as part of
        # the error message. I REALLY don't want to parse an error string to find the index to
        # drop. Also, ME only verifies / creates the indexes in bulk - there's no way to
        # iterate through the index definitions and try them one by one. Since our indexes
        # should be small and built in the background anyway we're just gonna redo all of them

        try:
            db = get_db()
            db[document_class.__name__.lower()].drop_indexes()
            logger.warning('Dropped indexes for %s collection', document_class.__name__)
        except OperationFailure:
            logger.error('Dropping %s indexes failed, please check the database configuration',
                         document_class.__name__)
            raise

        # For bg-utils 2.3.3 -> 2.3.4 upgrade
        # We need to create the `has_parent` field
        if document_class == Request:
            logger.warning('Request definition is out of date, updating')
            _update_request_model()

        try:
            document_class.ensure_indexes()
            logger.warning('%s indexes rebuilt successfully', document_class.__name__)
        except OperationFailure:
            logger.error('%s index rebuild failed, please check the database configuration',
                         document_class.__name__)
            raise


def _verify_db():
    """Do everything necessary to ensure the database is in a 'good' state"""
    from .models import Job, Request, Role, System

    for doc in (Job, Request, Role, System):
        _check_indexes(doc)

    _ensure_roles()
    _ensure_users()
