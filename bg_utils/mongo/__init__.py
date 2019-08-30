from bg_utils.mongo.util import verify_db


def setup_database(config):
    """Attempt connection to a Mongo database and verify necessary indexes

    Args:
        config (box.Box): Yapconf-generated configuration object

    Returns:
        bool: True if successful, False otherwise (unable to connect)

    Raises:
        Any mongoengine or pymongo error *except* ConnectionFailure,
        ServerSelectionTimeoutError
    """
    from mongoengine import connect, register_connection
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

    try:
        # Set timeouts here to a low value - we don't want to wait 30
        # seconds if there's no database
        conn = connect(
            alias="aliveness",
            db=config.db.name,
            socketTimeoutMS=1000,
            serverSelectionTimeoutMS=1000,
            **config.db.connection
        )

        # The 'connect' method won't actually fail
        # An exception won't be raised until we actually try to do something
        conn.server_info()

        # Close the aliveness connection - the timeouts are too low
        conn.close()
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False

    # Now register the default connection with real timeouts
    # Yes, mongoengine uses 'db' in connect and 'name' in register_connection
    register_connection("default", name=config.db.name, **config.db.connection)

    try:
        guest_login_enabled = config.auth.guest_login_enabled
    except KeyError:
        guest_login_enabled = None

    verify_db(guest_login_enabled)

    return True
