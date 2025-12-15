# -*- coding: utf-8 -*-
from brewtils.models import Events

accepted_forwarding_events = [
    Events.GARDEN_STARTED.name,
    Events.GARDEN_STOPPED.name,
    Events.GARDEN_SYNC.name,
    Events.GARDEN_UPDATED.name,
    Events.INSTANCE_INITIALIZED.name,
    Events.INSTANCE_STARTED.name,
    Events.INSTANCE_STOPPED.name,
    Events.INSTANCE_UPDATED.name,
    Events.REQUEST_CANCELED.name,
    Events.REQUEST_COMPLETED.name,
    Events.REQUEST_CREATED.name,
    Events.REQUEST_DELETED.name,
    Events.REQUEST_STARTED.name,
    Events.REQUEST_TOPIC_PUBLISH.name,
    Events.REQUEST_UPDATED.name,
    Events.SYSTEM_CREATED.name,
    Events.SYSTEM_REMOVED.name,
    Events.SYSTEM_UPDATED.name,
]
