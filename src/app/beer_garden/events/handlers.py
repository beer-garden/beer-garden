# -*- coding: utf-8 -*-
import logging

from mongoengine import DoesNotExist, NotUniqueError

from beer_garden.db.mongo import models as mongo_models
from brewtils import models as brewtils_models
from brewtils.models import Event, Events

import beer_garden.config
import beer_garden.garden
import beer_garden.router
import beer_garden.db.api as db
from beer_garden.local_plugins.manager import PluginManager

logger = logging.getLogger(__name__)


def garden_callbacks(event: Event) -> None:
    """Callbacks for events

    Args:
        event: The event

    Returns:
        None
    """

    if event.name in (Events.SYSTEM_CREATED.name,):
        beer_garden.garden.garden_add_system(event.payload, event.garden)

    if event.name in (
        Events.GARDEN_CREATED.name,
        Events.GARDEN_STARTED.name,
        Events.GARDEN_UPDATED.name,
    ):
        # Only accept local garden updates and the garden sending the event
        # This should prevent grand-child gardens getting into the database

        if event.payload.name == event.garden and event.payload.name != beer_garden.config.get("garden.name"):
            garden = beer_garden.garden.get_garden(event.payload.name)
            if garden is None:
                beer_garden.garden.create_garden(event.payload)

    elif event.name in (Events.GARDEN_REMOVED.name,):
        # Only accept local garden updates and the garden sending the event
        # This should prevent grand-child gardens getting into the database
        if event.payload.name in [event.garden, beer_garden.config.get("garden.name")]:
            beer_garden.router.remove_garden(event.payload)

    # Subset of events we only care about if they originate from the local garden
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

    # Subset of events we only care about if they originate from a downstream garden
    else:
        if event.error:
            logger.error(
                f"Downstream error event ({event} : {event.payload_type}: {event.payload}): {event.error_message}"
            )
            return

        if event.name in (Events.REQUEST_CREATED.name, Events.SYSTEM_CREATED.name):
            try:
                db.create(event.payload)
            except NotUniqueError:
                logger.error(
                    f"Unable to process ({event} : {event.payload_type} : {event.payload}): Object already exists in database"
                )

        elif event.name in (
            Events.REQUEST_STARTED.name,
            Events.REQUEST_COMPLETED.name,
            Events.SYSTEM_UPDATED.name,
            Events.INSTANCE_UPDATED.name,
        ):
            if not event.payload_type:
                logger.error(
                    f"Unable to process event ({event} : {event.payload_type}: {event.payload}): No Payload Type"
                )
                return

            model_class = getattr(brewtils_models, event.payload_type)
            record = db.query_unique(model_class, id=event.payload.id)

            if record:
                db.update(event.payload)
            else:
                logger.error(
                    f"Unable to update ({event} : {event.payload_type} : {event.payload}): Object does not exist in database"
                )

        elif event.name in (Events.SYSTEM_REMOVED.name,):

            if not event.payload_type:
                logger.error(
                    f"Unable to process event ({event} : {event.payload_type}: {event.payload}): No Payload Type"
                )
                return

            model_class = getattr(brewtils_models, event.payload_type)
            record = db.query_unique(model_class, id=event.payload.id)

            if record:
                db.delete(event.payload)
            else:
                logger.error(
                    f"Unable to delete ({event} : {event.payload_type} : {event.payload}): Object does not exist in database"
                )
