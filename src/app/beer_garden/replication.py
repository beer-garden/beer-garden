import beer_garden.db.api as db
import os
import beer_garden.config as config
from uuid import uuid4
from brewtils.models import Replication
from datetime import datetime, timedelta, timezone

def get_replication_id() ->str:
    replication_id = os.environ.get('BG_REPLICATION_ID', None)

    if not replication_id:
        replication_id = str(uuid4())
        os.environ['BG_REPLICATION_ID'] = replication_id
    return replication_id

def get_replication(replication_id = None) -> Replication:
    if not replication_id:
        replication_id = get_replication_id()
    return db.query_unique(Replication, replication_id = replication_id)

def update_heartbeat() -> Replication:

    replication_id = get_replication_id()

    replication = db.query_unique(Replication, replication_id=replication_id, raise_missing=False)

    if not replication:
        # TODO: Revert back to 30 seconds
        return db.create(Replication(replication_id=replication_id, expires_at=datetime.now(timezone.utc) + timedelta(seconds=120) ))
    else:
        replication.expires_at=datetime.now(timezone.utc) + timedelta(seconds=30)
        return db.update(replication)
