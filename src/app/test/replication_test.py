import os

from beer_garden.replication import (
    get_replication_id,
    create_replication,
    get_replications,
    update_replication,
)
from brewtils.models import Replication
from datetime import datetime, timedelta, timezone


class TestReplication(object):

    def test_get_replication_id(self):

        if "BG_REPLICATION_ID" in os.environ:
            del os.environ["BG_REPLICATION_ID"]

        replication_id = get_replication_id()

        assert replication_id == os.environ["BG_REPLICATION_ID"]

    def test_replication_expiration(self):
        create_replication(
            Replication(
                replication_id="1111",
                expires_at=datetime.now(timezone.utc) - timedelta(seconds=10),
            )
        )

        assert len(get_replications()) == 0

    def test_update_replication(self):
        replication = create_replication(
            Replication(
                replication_id="1111",
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=100),
            )
        )

        replication.replication_id = "2222"
        update_replication(replication)

        db_replications = get_replications()
        assert len(db_replications) == 1
        assert db_replications[0].replication_id == "2222"
