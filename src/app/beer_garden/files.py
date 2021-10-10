# -*- coding: utf-8 -*-

from base64 import b64decode, b64encode
from datetime import datetime
from math import ceil
from typing import Any, Callable, Dict, List, Union

from brewtils.errors import ModelValidationError, NotFoundError
from brewtils.models import (
    Event,
    Events,
    File,
    FileChunk,
    FileStatus,
    Job,
    Operation,
    Request,
)
from bson import ObjectId
from bson.errors import InvalidId

import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.errors import NotUniqueException

MAX_CHUNK_SIZE = 1024 * 1024 * 15  # 15MB
OWNERSHIP_PRIORITY = {
    "JOB": 1,
    "REQUEST": 2,
}
OWNERSHIP_MAP = {
    "JOB": Job,
    "REQUEST": Request,
}


def _unroll_object(
    obj: object,
    key_map: Dict[str, Union[str, Callable[[dict, str], Any]]] = None,
    ignore: List[str] = None,
) -> dict:
    """Returns an altered obj __dict__

    Args:
        obj: The object to unroll into a dictionary.
        key_map: A map to transform a set of keys to another key.
                 Valid values are new keys or functions of the signature func(dict, key)
                 the function is expected to alter the dict in-place.
                 (e.g. {'original_key': 'new_key', 'other_key': func})
        ignore: List of keys to be excluded

    Returns:
        The altered __dict__
    """
    if key_map is None:
        key_map = {}

    if ignore is None:
        ignore = []

    ret = {}
    for (key, val) in obj.__dict__.items():
        if key in key_map:
            if callable(key_map[key]):
                key_map[key](ret, val)
            else:
                ret[key_map[key]] = val
        elif key not in ignore:
            ret[key] = val

    return ret


def _safe_build_object(cls, *objects, ignore=None, **manual_kwargs):
    if ignore is None or type(ignore) is not list:
        ignore = []

    kwargs = {}
    for obj in objects:
        if type(obj) is File:
            kwargs.update(
                _unroll_object(
                    obj,
                    key_map={"id": "file_id"},
                    ignore=["job", "owner", "request", "updated_at"] + ignore,
                )
            )

        elif type(obj) is FileChunk:
            kwargs.update(
                _unroll_object(
                    obj,
                    key_map={"id": "chunk_id"},
                    ignore=["owner", "job", "request"] + ignore,
                )
            )

        else:
            kwargs.update(_unroll_object(obj))

    kwargs.update(manual_kwargs)

    return cls(**kwargs)


def check_file(file_id: str, upsert: bool = False) -> File:
    """Checks that the file with file_id exists in the DB

    Args:
        file_id: The id for the requested file.
        upsert: If the file doesn't exist create a placeholder file

    Returns:
        The file object

    Raises:
        NotFoundError: File with the requested ID doesn't exist and is expected to
        ModelValidationError: Incorrectly formatted ID is given
    """
    try:
        ObjectId(file_id)
    except (InvalidId, TypeError):
        raise ModelValidationError(
            f"Cannot create a file id with the string {file_id}. "
            "Requires 24-character hex string."
        )

    res = db.query_unique(File, id=file_id)

    if res is None:
        if upsert:
            create_file("BG_placeholder", 0, 0, file_id)
            res = db.query_unique(File, id=file_id)
        else:
            raise NotFoundError(f"Tried to fetch an unsaved file {file_id}")

        db.modify(res, updated_at=datetime.utcnow())

    return res


def check_chunk(chunk_id: str):
    """Checks that the file with file_id exists in the DB

    Args:
        chunk_id: The id for the requested chunk.

    Returns:
        The file object.

    Raises:
        NotFoundError: Chunk with the requested ID doesn't exist.
        ModelValidationError: Incorrectly formatted ID is given
    """
    try:
        ObjectId(chunk_id)
    except (InvalidId, TypeError):
        raise ModelValidationError(
            f"Cannot create a chunk id with the string {chunk_id}. "
            "Requires 24-character hex string."
        )

    return db.query_unique(FileChunk, id=chunk_id, raise_missing=True)


def check_chunks(file_id: str):
    """Checks that the file with file_id has a valid chunks field

    Args:
        file_id: Valid file id.

    Returns:
        The wrapped function.

    Raises:
        NotFoundError: File with the requested ID doesn't exist and is expected to
        ModelValidationError: File with the requested ID has no associated file chunks
    """
    res = check_file(file_id)

    if res.chunks is None:
        raise ModelValidationError(
            f"Tried to load a file {res.id} with no associated chunks."
        )

    return res


def create_chunk(
    file_id: str, offset: int = None, data: str = None, **kwargs
) -> FileStatus:
    """Saves provided chunk to the DB, updates the parent document with the chunk id

    Args:
        file_id: This should be a valid file id.
        offset: The offset index. (e.g. 0, 1, 2, ...)
        data: The base64 encoded data
        kwargs: The other parameters for FileChunk that we don't need to check

    Raises:
        NotFoundError: File with the requested ID doesn't exist and is expected to
    """
    if len(data) > MAX_CHUNK_SIZE:
        return FileStatus(
            operation_complete=False,
            message=(
                "Chunk data length exceeds the maximum "
                f"allowable length of {MAX_CHUNK_SIZE}."
            ),
            file_id=file_id,
            offset=offset,
            data=data,
        )

    file = check_file(file_id, upsert=kwargs.get("upsert", False))
    chunk = FileChunk(
        file_id=file.id, offset=offset, data=data, owner=kwargs.get("owner", None)
    )

    # This is starting to get DB-specific, but we want to be sure this is an atomic operation.
    chunk = db.create(chunk)
    modify = {f"set__chunks__{offset}": chunk.id}
    file = db.modify(file, **modify)
    chunk = db.modify(chunk, owner=file.id)

    return _safe_build_object(FileStatus, file, chunk, operation_complete=True)


def _verify_chunks(file_id: str) -> FileStatus:
    """Processes the requested file to determine if any chunks are missing

    Args:
        file_id: Valid file id

    Returns:
        A dictionary that describes the validity of the file

    Raises:
        NotFoundError: File with the requested ID doesn't exist and is expected to
        ModelValidationError: File with the requested ID has no associated chunks
    """
    file = check_chunks(file_id)
    num_chunks = ceil(file.file_size / file.chunk_size)
    computed_size = file.chunk_size * num_chunks

    size_ok = file.file_size <= computed_size
    length_ok = num_chunks == len(file.chunks)

    missing = [
        x for x in range(len(file.chunks)) if file.chunks.get(str(x), None) is None
    ]

    return _safe_build_object(
        FileStatus,
        file,
        operation_complete=True,
        valid=(length_ok and missing == [] and size_ok),
        missing_chunks=missing,
        expected_max_size=computed_size,
        size_ok=size_ok,
        expected_number_of_chunks=num_chunks,
        number_of_chunks=len(file.chunks),
        chunks_ok=length_ok,
    )


def _fetch_chunk(file_id: str, chunk_num: int) -> FileStatus:
    """Fetches a single chunk of the requested file

    Args:
        file_id: This should be a valid file id.
        chunk_num: The offset index. (e.g. 0, 1, 2, ..)

    Returns:
        The chunk data.

    Raises:
        NotFoundError: File with the requested ID doesn't exist and is expected to
        ModelValidationError: File with the requested ID has no associated chunks
        ValueError: Chunk number requested is not associated with the given file
    """
    file = check_chunks(file_id)
    if str(chunk_num) in file.chunks:
        chunk = check_chunk(file.chunks[str(chunk_num)])
        return _safe_build_object(
            FileStatus,
            chunk,
            operation_complete=True,
        )
    else:
        raise ValueError(f"Chunk number {chunk_num} is invalid for file {file.id}")


def _fetch_file(file_id: str) -> FileStatus:
    """Fetches the entire requested file

    Args:
        file_id: This should be a valid file id.

    Returns:
        The file data if the file is valid; None otherwise.

    Raises:
        NotFoundError: File with the requested ID doesn't exist and is expected to.
        ModelValidationError: File with the requested ID has no associated chunks.
    """
    # This is going to get big, try our best to be efficient
    check = _verify_chunks(file_id)

    if check.valid:
        file = check_chunks(file_id)
        all_data = [
            db.query_unique(FileChunk, id=file.chunks[str(x)]).data
            for x in range(len(file.chunks))
        ]

        return _safe_build_object(
            FileStatus,
            file,
            operation_complete=True,
            # Each chunk should be base64 encoded, and
            # we can't just concat those strings.
            data=b64encode(b"".join(map(b64decode, all_data))).decode("utf-8"),
        )
    else:
        return check


def create_file(
    file_name: str,
    file_size: int,
    chunk_size: int,
    file_id: str = None,
    upsert: bool = False,
    **kwargs,
) -> FileStatus:
    """Creates a top-level File object to track chunks

    Args:
        file_name: The name of the file to be uploaded.
        file_size: The size of the file to be uploaded (in bytes).
        chunk_size: The size of the chunks that the file is broken into (in bytes).
        file_id: (Optional) The original file id
        upsert: (Optional) If a file ID is given, the function will
                modify the file metadata if it already exists
        kwargs: (Optional) Any other valid file fields that can be populated

    Returns:
        A dictionary with the id

    Raises:
        ValueError: Chunk size provided exceeds the size allowed
        ModelValidationError: File id (if provided) is not a valid ObjectId string
        NotUniqueException: File with the requested ID already exists
    """
    if chunk_size > MAX_CHUNK_SIZE:
        raise ValueError(
            f"Cannot create a file with chunk size greater than {MAX_CHUNK_SIZE}."
        )

    file = File(
        file_name=file_name,
        file_size=file_size,
        chunk_size=chunk_size,
        **kwargs,
    )

    # Override the file id if passed in
    if file_id is not None:
        try:
            file.id = ObjectId(file_id)
        except (InvalidId, TypeError):
            raise ModelValidationError(
                f"Cannot create a file id with the string {file_id}. "
                "Requires 24-character hex string."
            )
    # Normal creation process, checks for uniqueness
    if not upsert:
        try:
            file = db.create(file)
        except NotUniqueException:
            raise NotUniqueException(
                f"Cannot create a file with id {file_id}; file with id already exists."
            )
        return _safe_build_object(FileStatus, file, operation_complete=True)

    # Safe creation process, handles out-of-order file uploads but may
    # combine existing data with collision
    else:
        res = db.query_unique(File, id=file.id)
        if res is None:
            file = db.create(file)
        else:
            file = db.modify(
                res,
                **_unroll_object(
                    file,
                    ignore=["id", "chunks", "owner", "job", "request", "updated_at"],
                ),
            )

        return _safe_build_object(FileStatus, file, operation_complete=True)


def fetch_file(file_id: str, chunk: int = None, verify: bool = False) -> FileStatus:
    """Fetches file information

    Args:
        file_id: The id of the file to fetch
        chunk: (Optional) If included, fetches a single chunk instead of the entire file.
        verify: (Optional) If included, fetches file validity information instead of data.

    Returns:
        The requested information, unless an error occurs.
        (Actual contents determined by optional flags)
    """
    if verify:
        return _verify_chunks(file_id)

    if chunk is not None:
        return _fetch_chunk(file_id, chunk)

    else:
        return _fetch_file(file_id)


def delete_file(file_id: str) -> FileStatus:
    """Deletes a file and its chunks

    Args:
        file_id: The id of the file.
    """
    file = check_file(file_id)

    # This should delete the associated chunks as well.
    db.delete(file)

    return FileStatus(operation_complete=True, file_id=file_id)


def set_owner(file_id: str, owner_id: str = None, owner_type: str = None) -> FileStatus:
    """Sets the owner field of the file.

    This is used for DB pruning.

    Args:
        file_id: The id of the file.
        owner_id: The id of the owner.
        owner_type: The type of the owner (job/request).
    """
    if (owner_id is not None) and (owner_type is not None):
        file = check_file(file_id)
        old_owner_priority = OWNERSHIP_PRIORITY.get(file.owner_type, 1_000_000)
        new_owner_priority = OWNERSHIP_PRIORITY.get(owner_type, 1_000_000)

        # Case 1 : New owner has equal or higher priority
        # Case 2 : The old owner is a higher priority than the new one, but it was deleted.
        if new_owner_priority <= old_owner_priority or (
            file.owner_type in OWNERSHIP_PRIORITY
            and (file.job is None and file.request is None)
        ):
            if owner_type in OWNERSHIP_MAP:
                owner = db.query_unique(OWNERSHIP_MAP[owner_type], id=owner_id)
                file = db.modify(
                    file,
                    owner_id=owner_id,
                    owner_type=owner_type,
                    job=owner.id if owner is not None and owner_type == "JOB" else None,
                    request=owner.id
                    if owner is not None and owner_type == "REQUEST"
                    else None,
                )
            else:
                file = db.modify(file, owner_id=owner_id, owner_type=owner_type)

            return _safe_build_object(FileStatus, file, operation_complete=True)

        return _safe_build_object(
            FileStatus,
            operation_complete=False,
            message=(
                f"Owner type {owner_type} has lower priority than {file.owner_type}"
            ),
        )

    return _safe_build_object(
        FileStatus,
        operation_complete=False,
        message=(
            "Operation FILE_OWN requires an owner type "
            f"and id. Got {owner_type} and {owner_id}"
        ),
    )


def _find_chunk_params(param_values) -> List[str]:
    """Look through parameter values for chunk Resolvables

    Args:
        param_values: The parameter values to be scanned

    Returns:
        A list of file ids (may be empty).
    """
    ids = []

    # Resolvables can only be dicts, so we only care about those
    if isinstance(param_values, dict):
        if param_values.get("type") == "chunk":
            ids.append(param_values.get("details", {}).get("file_id"))

        # If it's not a resolvable it might be a model, so recurse down and check
        else:
            for value in param_values.values():
                ids += _find_chunk_params(value)

    return ids


def forward_file(operation: Operation) -> None:
    """Send file data before forwarding an operation with a file parameter."""

    # HEADS UP - THIS IS PROBABLY BROKEN
    # import here bypasses circular dependency
    import beer_garden.router as router

    for file_id in _find_chunk_params(operation.model.parameters):
        file = check_chunks(file_id)
        args = [file.file_name, file.file_size, file.chunk_size]
        # Make sure we get all of the other data
        kwargs = _safe_build_object(
            dict,
            file,
            ignore=[
                "file_name",
                "file_size",
                "chunk_size",
            ],
            upsert=True,
        )

        file_op = Operation(
            operation_type="FILE_CREATE",
            args=args,
            kwargs=kwargs,
            target_garden_name=operation.target_garden_name,
            source_garden_name=operation.source_garden_name,
        )

        # This should put push the file operations before the current one
        router.forward_processor.put(file_op)

        for chunk_id in file.chunks.values():
            chunk = check_chunk(chunk_id)
            c_args = [chunk.file_id, chunk.offset, chunk.data]
            c_kwargs = _safe_build_object(
                dict, chunk, ignore=["file_id", "offset", "data"], upsert=True
            )

            chunk_op = Operation(
                operation_type="FILE_CHUNK",
                args=c_args,
                kwargs=c_kwargs,
                target_garden_name=operation.target_garden_name,
                source_garden_name=operation.source_garden_name,
            )

            # This should put push the file operations before the current one
            router.forward_processor.put(chunk_op)


def handle_event(event: Event) -> None:
    """Handle events"""
    if event.garden == config.get("garden.name"):
        if event.name == Events.JOB_CREATED.name:
            for file_id in _find_chunk_params(
                event.payload.request_template.parameters
            ):
                set_owner(file_id, owner_id=event.payload.id, owner_type="JOB")

        if event.name == Events.REQUEST_CREATED.name:
            for file_id in _find_chunk_params(event.payload.parameters):
                set_owner(file_id, owner_id=event.payload.id, owner_type="REQUEST")
