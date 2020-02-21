# -*- coding: utf-8 -*-
import logging

from mongoengine import DoesNotExist

from beer_garden.db.mongo import models as mongo_models
from brewtils import models as brewtils_models
from brewtils.models import Event, Events

import beer_garden.config
import beer_garden.db.api as db
from beer_garden.local_plugins.manager import PluginManager

logger = logging.getLogger(__name__)


def local_callbacks(event: Event) -> None:
    """Callbacks for events originating from the local garden

    Args:
        event: The event

    Returns:
        None
    """
    if event.garden == beer_garden.config.get("garden.name"):
        if event.error:
            logger.error(f"Local error event ({event}): {event.error_message}")
            return

        try:
            # Start local plugins after the entry point comes up
            if event.name == Events.ENTRY_STARTED.name:
                PluginManager.instance().start_all()
            elif event.name == Events.INSTANCE_INITIALIZED.name:
                PluginManager.instance().associate(event)
            elif event.name == Events.INSTANCE_STARTED.name:
                PluginManager.instance().do_start(event)
            elif event.name == Events.INSTANCE_STOPPED.name:
                PluginManager.instance().do_stop(event)
        except Exception as ex:
            logger.exception(f"Error executing local callback for {event}: {ex}")


def downstream_callbacks(event: Event) -> None:
    """Callbacks for events originating from downstream gardens

    Args:
        event: The event

    Returns:
        None
    """
    if event.garden != beer_garden.config.get("garden.name"):
        if event.error:
            logger.error(
                f"Downstream error event ({event} : {event.payload}): {event.error_message}"
            )
            return

        if not event.payload_type:
            logger.error(
                f"Unable to process event ({event} : {event.payload}): No Payload Type"
            )
            return

        # Grab the mongo DB model of the object
        mongo_model_class_ = getattr(mongo_models, event.payload_type)
        brewtils_model_class_ = getattr(brewtils_models, event.payload_type)

        # Check model for unique fields
        if mongo_model_class_._meta and mongo_model_class_._meta["indexes"]:

            for index in mongo_model_class_._meta["indexes"]:
                if index["unique"]:
                    query_kwargs = {}
                    for field in index["fields"]:
                        query_kwargs[field] = getattr(event.payload, field)

                    try:
                        db_obj = db.query_unique(brewtils_model_class_, **query_kwargs)

                        if db_obj and db_obj.id is not event.payload.id:
                            logger.error(
                                f"Unable to process ({event} : {event.payload}): Object already exists in database"
                            )
                            return

                    except DoesNotExist:
                        # If the record does not exist, then move forward with action
                        pass

        try:

            if event.name in (Events.REQUEST_CREATED.name, Events.SYSTEM_CREATED.name):
                db.create(event.payload)

            elif event.name in (
                Events.REQUEST_STARTED.name,
                Events.REQUEST_COMPLETED.name,
                Events.SYSTEM_UPDATED.name,
                Events.INSTANCE_UPDATED.name,
            ):
                db.update(event.payload)

            elif event.name in (Events.SYSTEM_REMOVED.name,):
                db.delete(event.payload)
        except Exception as ex:
            logger.exception(f"Error executing downstream callback for {event}: {ex}")


def system_mapping_callback(event: Event) -> None:
    """
    Callback to name new Systems to Gardens
    Args:
        event:

    Returns:
        None

    """

    if event.name in Events.SYSTEM_CREATED.name:
        beer_garden.garden.garden_add_system(event.payload, event.garden)

        # Caches routing information
        beer_garden.router.update_system_mapping(event.payload, event.garden)


def garden_mapping_callback(event: Event) -> None:
    """
    Callback to cache Garden Routing Information
    Args:
        event:

    Returns:
        None

    """

    if event.name in (Events.GARDEN_CREATED.name, Events.GARDEN_UPDATED.name):
        beer_garden.router.update_garden_connection(event.payload)

    elif event.name in Events.GARDEN_REMOVED.name:
        beer_garden.router.remove_garden_connection(event.payload)
