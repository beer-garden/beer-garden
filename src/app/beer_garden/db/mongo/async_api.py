# -*- coding: utf-8 -*-
from typing import Optional

from box import Box
from pymongo import AsyncMongoClient

async_db: Optional[AsyncMongoClient] = None


def create_connection(db_config: Box = None) -> None:
    """Register a database connection

    Args:
        db_config: Yapconf-generated configuration object

    Returns:
        None
    """
    global async_db

    async_conn = AsyncMongoClient(
        host=db_config.connection.host,
        port=db_config.connection.port,
        username=db_config.connection.username,
        password=db_config.connection.password,
        authSource=db_config.connection.authentication_source,
        tz_aware=True,
    )
    async_db = async_conn[db_config.name]


async def query(
    collection: str = None, filter: dict = None, projection: dict = None
) -> dict:
    """Query for a single document

    Args:
        collection: Name of collection to query
        filter: Filter parameters
        projection: Projection parameters

    Returns:
        Dict of the find_one result

    """
    return await async_db[collection].find_one(filter=filter, projection=projection)


async def update_one(
    collection: str = None, filter: dict = None, update: dict = None
) -> None:
    """Update a single document

    Args:
        collection: Name of collection to modify
        filter: Filter parameters
        update: Update parameter

    Returns:
        None

    """
    return await async_db[collection].update_one(filter=filter, update=update)
