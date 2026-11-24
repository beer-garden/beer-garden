import io

from brewtils.models import Resolvable
from bson import ObjectId

import beer_garden.db.api as db


def create_raw_file(contents: io.BytesIO):
    file_id = db.gridfs_put(contents)

    return Resolvable(id=str(file_id), type="bytes", storage="gridfs")


def read_raw_file(file_id: str):
    return db.gridfs_read({"_id": ObjectId(file_id)}, load_json=False)


def delete_raw_file(file_id: str):
    db.gridfs_delete({"_id": ObjectId(file_id)})
