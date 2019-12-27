# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from brewtils.errors import ModelValidationError
from brewtils.models import Events, Namespace, PatchOperation, System


import beer_garden.db.api as db
from beer_garden.events.events_manager import publish_event

logger = logging.getLogger(__name__)


def get_namespace(namespace_label: str) -> Namespace:
    """Retrieve an individual Namespace

    Args:
        namespace_label: The label of namespace

    Returns:
        The Namespace

    """
    return db.query_unique(Namespace, namespace=namespace_label)


def update_namespace(namespace_label: str, patch: PatchOperation) -> Namespace:
    """Applies updates to an instance.

    Args:
        namespace_label: The Namespace Label
        patch: Patch definition to apply

    Returns:
        The updated Instance
    """
    namespace = None

    for op in patch:
        operation = op.operation.lower()

        if operation in ["initializing", "running", "stopped", "block"]:
            namespace = update_namespace_status(namespace_label, operation.upper())
        elif operation == "heartbeat":
            namespace = update_namespace_status(namespace_label, "RUNNING")

        else:
            raise ModelValidationError(f"Unsupported operation '{op.operation}'")

    return namespace


@publish_event(Events.NAMESPACE_UPDATED)
def update_namespace_status(namespace_label: str, new_status: str) -> Namespace:
    """Update an Instance status.

    Will also update the status_info heartbeat.

    Args:
        instance_id: The Instance ID
        new_status: The new status

    Returns:
        The updated Instance
    """
    namespace = db.query_unique(Namespace, namespace=namespace_label)
    namespace.status = new_status
    namespace.status_info["heartbeat"] = datetime.utcnow()

    namespace = db.update(namespace)
    logger.info("Downstream Namespace " + namespace_label + " is now " + new_status)
    return namespace


@publish_event(Events.NAMESPACE_REMOVED)
def remove_namespace(namespace_label: str) -> None:
    """Remove a namespace

        Args:
            namespace_label: The Namespace Label

        Returns:
            None

        """
    namespace = db.query_unique(Namespace, namespace=namespace_label)
    db.delete(namespace)


@publish_event(Events.NAMESPACE_CREATED)
def create_namespace(namespace: Namespace) -> Namespace:
    """Create a new Namespace

    Args:
        namespace: The Namespace to create

    Returns:
        The created Namespace

    """

    namespace.status = "INITIALIZING"
    namespace.status_info["heartbeat"] = datetime.utcnow()
    db_namespace = db.query_unique(Namespace, namespace=namespace.namespace)
    if db_namespace:
        db_namespace.status = namespace.status
        db_namespace.status_info = namespace.status_info
        db_namespace.connection_type = namespace.connection_type
        db_namespace.connection_params = namespace.connection_params

        namespace = db.update(db_namespace)
    else:
        namespace = db.create(namespace)

    return namespace
