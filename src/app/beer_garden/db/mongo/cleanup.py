import logging

from mongoengine.connection import get_db

logger = logging.getLogger(__name__)


def get_stats(collection_name):
    """
    Return db stats about a collection
    """
    db = get_db()
    stats = db.command({"collStats": collection_name})
    return {
        "count": stats["count"],
        "size": stats["size"],
        "storageSize": stats["storageSize"],
        "nindexes": stats["nindexes"],
        "totalIndexSize": stats["totalIndexSize"],
    }


def validate_collection_names(collection_names=None):
    """
    Make sure any collection names provided are valid
    """
    db = get_db()
    valid_collection_names = db.list_collection_names()
    if collection_names:
        invalid_names = list(set(collection_names) - set(valid_collection_names))
        if invalid_names:
            raise ValueError(f"Collection name(s) {invalid_names} do not exist")
        else:
            return collection_names
    else:
        return valid_collection_names


def compact(collection_names=None, execute=False):
    """
    Runs mongodb compact operation
    mongod rebuilds all indexes in parallel following the compact operation.
    """
    db = get_db()
    results = {}
    collection_names = validate_collection_names(collection_names)
    for collection_name in collection_names:
        results[collection_name] = {}
        logger.info(f"Before {collection_name} compact: {get_stats(collection_name)}")
        results[collection_name]["before"] = get_stats(collection_name)
        if execute:
            db.command({"compact": collection_name})
            logger.info(
                f"After {collection_name} compact: {get_stats(collection_name)}"
            )
            results[collection_name]["after"] = get_stats(collection_name)

    return results


def reindex(collection_names=None, execute=False):
    """
    Run mongodb reIndex operation
    """
    db = get_db()
    results = {}
    collection_names = validate_collection_names(collection_names)
    for collection_name in collection_names:
        results[collection_name] = {}
        logger.info(f"Before {collection_name} reIndex: {get_stats(collection_name)}")
        results[collection_name]["before"] = get_stats(collection_name)
        if execute:
            db.command({"reIndex": collection_name})
            logger.info(
                f"After {collection_name} reIndex: {get_stats(collection_name)}"
            )
            results[collection_name]["after"] = get_stats(collection_name)

    return results
