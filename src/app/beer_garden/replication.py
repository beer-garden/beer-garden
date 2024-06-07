import beer_garden.db.api as db
import os
import beer_garden.config as config
from uuid import UUID, uuid4
from brewtils.models import Replication
from datetime import datetime, timedelta, timezone

def get_repliation_id() ->str:
    replication_id = os.environ.get('BG_REPLICATION_ID', None)

    if not replication_id:
        replication_id = str(uuid4())
        os.environ['BG_REPLICATION_ID'] = replication_id
    return replication_id

def get_replications() -> list[Replication]:
    return db.query(Replication)

def update_heartbeat() -> None:

    replication_id = get_repliation_id()

    replication = db.query_unique(Replication, replication_id=replication_id, raise_missing=False)

    if not replication:
        replication = Replication(replication_id=replication_id, expires_at=datetime.now(timezone.utc) + timedelta(minutes=config.get("replication.expires_at")) )
        db.create(replication)
    else:
        replication.expires_at=datetime.now(timezone.utc) + timedelta(minutes=config.get("replication.expires_at"))
        db.update(replication)
