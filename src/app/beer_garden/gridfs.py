import io

from brewtils.models import Request, Resolvable
from bson import ObjectId

import beer_garden.db.api as db


def create_gridfs(contents, **kwargs):
    db.gridfs_create(model=contents, **kwargs)


def create_raw_file(contents: io.BytesIO):
    file_id = db.gridfs_put(contents)

    return Resolvable(id=str(file_id), type="bytes", storage="gridfs")


def read_raw_file(file_id: str):
    return read_gridfs({"_id": ObjectId(file_id)}, load_json=False)


def read_gridfs(filter, **kwargs):

    return db.gridfs_read(filter, **kwargs)


def delete_gridfs_raw_file(file_id: str):
    db.gridfs_delete({"_id": ObjectId(file_id)})


def delete_gridfs_request(request: Request):
    delete_gridfs({"request_id": request.id})


def delete_gridfs(filter):
    db.gridfs_delete(filter=filter)


def update_associated_raw_file(file_id: str, request: Request):
    db.gridfs_update_metadata(
        {"_id": ObjectId(file_id)},
        {
            "status": request.status,
            "updated_at": request.updated_at,
            "root_command_type": request.root_command_type,
            "file_type": "parameter",
            "request_id": request.id,
        },
    )


def update_associated_gridfs(request: Request):
    db.gridfs_update_metadata(
        {"request_id": request.id},
        {
            "status": request.status,
            "updated_at": request.updated_at,
            "root_command_type": request.root_command_type,
        },
    )


def exists_gridfs(filter):
    return db.gridfs_exists(filter)
