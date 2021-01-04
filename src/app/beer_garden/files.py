# -*- coding: utf-8 -*-
import six
from math import ceil
from bson import ObjectId
from bson.errors import InvalidId
from base64 import b64decode, b64encode
from datetime import datetime

import beer_garden.db.api as db
import beer_garden.config as config
import beer_garden.router as router
from beer_garden.errors import NotUniqueException
from brewtils.errors import ModelValidationError, NotFoundError
from brewtils.models import File, FileChunk, Request, Job, FileStatus, Events, Operation
from brewtils.resolvers.parameter import UI_FILE_ID_PREFIX


# 15MB
MAX_CHUNK_SIZE = 1024 * 1024 * 15
OWNERSHIP_PRIORITY = {
    "JOB": 1,
    "REQUEST": 2,
}
OWNERSHIP_MAP = {
    "JOB": Job,
    "REQUEST": Request,
}


def _format_id(dictionary, id):
    """
    Updates the given dictionary with the standard formatting for BG File IDs.
    """
    dictionary["file_id"] = f"{UI_FILE_ID_PREFIX} {id}"
    return dictionary


def _unroll_object(obj, key_map=None, ignore=None):
    """
    Reads the object __dict__ and uses the map or ignore
    fields to return an altered version of it.

    Parameters:
        obj: The object to unroll into a dictionary.
        key_map: A map to transform a set of keys to another key.
                 Valid values are new keys or functions of the signature func(dict, key);
                 the function is expected to alter the dict in-place.
                 (e.g. {'original_key': 'new_key', 'other_key': func})
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


def check_file(file_id: str, upsert: bool = False):
    """
    Checks that the file with file_id exists in the DB.

    Parameters:
        file_id: The id for the requested file.
        upsert: (Optional) If the file doesn't exist, create a
                placeholder file to be modified later.

    Returns:
        The file object.

    Raises:
        NotFoundError: Raised when a file with the requested
                       ID doesn't exist and is expected to.
        ModelValidationError: Raised when an ID is provided,
                              but is of the incorrect format.
    """
    if UI_FILE_ID_PREFIX in file_id:
        file_id = file_id.split(" ")[1]

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
            raise NotFoundError(f"Tried to fetch an unsaved file {file_id}.")
        db.modify(res, updated_at=datetime.utcnow())
    return res


def check_chunk(chunk_id: str):
    """
    Checks that the file with file_id exists in the DB.

    Parameters:
        chunk_id: The id for the requested chunk.

    Returns:
        The file object.

    Raises:
        NotFoundError: Raised when a chunk with the requested
                       ID doesn't exist.
        ModelValidationError: Raised when an ID is provided, but
                              is of the incorrect format.
    """
    if UI_FILE_ID_PREFIX in chunk_id:
        chunk_id = chunk_id.split(" ")[1]

    try:
        ObjectId(chunk_id)
    except (InvalidId, TypeError):
        raise ModelValidationError(
            f"Cannot create a chunk id with the string {chunk_id}. "
            "Requires 24-character hex string."
        )

    res = db.query_unique(FileChunk, id=chunk_id, raise_missing=True)
    return res


def check_chunks(file_id: str):
    """
    Checks that the file with file_id has a valid chunks field.

    Parameters:
        file_id: This should be a valid file id.

    Returns:
        The wrapped function.

    Raises:
        NotFoundError: Raised when a file with the requested
                       ID doesn't exist and is expected to.
        ModelValidationError: Raised when a file with the requested
                              ID doesn't have any associate file chunks.
    """
    res = check_file(file_id)
    if res.chunks is None:
        raise ModelValidationError(
            f"Tried to load a file {res.id} with no associated chunks."
        )
    return res


def _save_chunk(
    file_id: str, offset: int = None, upsert: bool = False, data: str = None, **kwargs
):
    """
    Saves the provided chunk data to the DB and updates
    the parent document with the chunk id.

    Parameters:
        file: This should be a valid file id.
        n: The offset index. (e.g. 0, 1, 2, ...)
        kwargs: The other parameters for FileChunk that we don't need to check

    Raises:
        NotFoundError: Raised when a file with the requested
                       ID doesn't exist and is expected to.
    """
    if len(data) > MAX_CHUNK_SIZE:
        return FileStatus(
            operation_complete=False,
            message=f"Chunk data length exceeds the maximum "
            f"allowable length of {MAX_CHUNK_SIZE}.",
            file_id=file_id,
            offset=offset,
            data=data,
            **kwargs,
        )

    file = check_file(file_id, upsert=upsert)
    chunk = FileChunk(file_id=file.id, offset=offset, data=data, **kwargs)
    c = db.create(chunk)
    # This is starting to get DB-specific, but we want to be sure this is an atomic operation.
    modify = {f"set__chunks__{offset}": c.id}
    file = db.modify(file, **modify)
    c = db.modify(c, owner=file.id)
    return FileStatus(
        operation_complete=True,
        # Splicing together the chunk and file metadata
        **dict(
            _unroll_object(c, key_map={"id": "chunk_id"}, ignore=["data", "owner"]),
            **_unroll_object(file, key_map={"id": _format_id}, ignore=["owner"]),
        ),
    )


def _verify_chunks(file_id: str):
    """
    Processes the requested file to determine if any chunks are missing.

    Parameters:
        file_id: This should be a valid file id.

    Returns:
        A dictionary that describes the validity of the file.

    Raises:
        NotFoundError: Raised when a file with the requested
                       ID doesn't exist and is expected to.
        ModelValidationError: Raised when a file with the requested
                              ID doesn't have any associate file chunks.
    """
    file = check_chunks(file_id)
    num_chunks = ceil(file.file_size / file.chunk_size)
    computed_size = file.chunk_size * num_chunks

    size_ok = file.file_size <= computed_size
    length_ok = num_chunks == len(file.chunks)

    missing = [
        x for x in range(len(file.chunks)) if file.chunks.get(str(x), None) is None
    ]
    return FileStatus(
        operation_complete=True,
        **_unroll_object(file, key_map={"id": _format_id}, ignore=["owner"]),
        valid=(length_ok and missing == [] and size_ok),
        missing_chunks=missing,
        expected_max_size=computed_size,
        size_ok=size_ok,
        expected_number_of_chunks=num_chunks,
        number_of_chunks=len(file.chunks),
        chunks_ok=length_ok,
    )


def _fetch_chunk(file_id: str, chunk_num: int):
    """
    Fetches a single chunk of the requested file.

    Parameters:
        file_id: This should be a valid file id.
        chunk_num: The offset index. (e.g. 0, 1, 2, ..)

    Returns:
        The chunk data.

    Raises:
        NotFoundError: Raised when a file with the requested
                       ID doesn't exist and is expected to.
        ModelValidationError: Raised when a file with the requested
                              ID doesn't have any associate file chunks.
        ValueError: Raised when the chunk number requested is not
                    associated with the given file.
    """
    file = check_chunks(file_id)
    if str(chunk_num) in file.chunks:
        chunk = check_chunk(file.chunks[str(chunk_num)])
        return FileStatus(
            operation_complete=True,
            **_unroll_object(chunk, key_map={"id": "chunk_id"}, ignore=["owner"]),
        )
    else:
        raise ValueError(f"Chunk number {chunk_num} is invalid for file {file.id}")


def _fetch_file(file_id: str):
    """
    Fetches the entire requested file.

    Parameters:
        file_id: This should be a valid file id.

    Returns:
        The file data, if the file is valid; None otherwise.

    Raises:
        NotFoundError: Raised when a file with the requested
                       ID doesn't exist and is expected to.
        ModelValidationError: Raised when a file with the requested
                              ID doesn't have any associate file chunks.
    """
    # This is going to get big, try our best to be efficient
    check = _verify_chunks(file_id)
    if check.valid:
        file = check_chunks(file_id)
        all_data = [
            db.query_unique(FileChunk, id=file.chunks[str(x)]).data
            for x in range(len(file.chunks))
        ]
        return FileStatus(
            operation_complete=True,
            **_unroll_object(file, key_map={"id": _format_id}, ignore=["owner"]),
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
):
    """
    Deletes the requested file and its corresponding chunks.

    Parameters:
        file_name: The name of the file to be uploaded.
        file_size: The size of the file to be uploaded (in bytes).
        chunk_size: The size of the chunks that the file is broken into (in bytes).
        file_id: (Optional) The original file id
        upsert: (Optional) If a file ID is given, the function will
                modify the file metadata if it already exists
        kwargs: (Optional) Any other valid file fields that can be populated

    Returns:
        A dictionary with the id.

    Raises:
        ValueError: Raised when the chunk size provided exceeds the size allowed.
        ModelValidationError: Raised when a file id (if provided)
                              is not a valid ObjectId string.
        NotUniqueException: Raised when a file with the requested ID already exists.
    """
    if chunk_size > MAX_CHUNK_SIZE:
        raise ValueError(
            f"Cannot create a file with chunk size greater than {MAX_CHUNK_SIZE}."
        )

    f = File(
        file_name=file_name,
        file_size=file_size,
        chunk_size=chunk_size,
        **kwargs,
    )

    # Override the file id if passed in
    if file_id is not None:
        if UI_FILE_ID_PREFIX in file_id:
            file_id = file_id.split(" ")[1]
        try:
            f.id = ObjectId(file_id)
        except (InvalidId, TypeError):
            raise ModelValidationError(
                f"Cannot create a file id with the string {file_id}. "
                "Requires 24-character hex string."
            )
    # Normal creation process, checks for uniqueness
    if not upsert:
        try:
            f = db.create(f)
        except NotUniqueException:
            raise NotUniqueException(
                f"Cannot create a file with id {file_id}; "
                "file with id already exists."
            )
        return FileStatus(
            operation_complete=True,
            **_unroll_object(f, key_map={"id": _format_id}, ignore=["owner"]),
        )

    # Safe creation process, handles out-of-order file uploads but may
    # combine existing data with collision
    else:
        res = db.query_unique(File, id=f.id)
        if res is None:
            f = db.create(f)
        else:
            f = db.modify(
                res, **_unroll_object(f, ignore=["id", "chunks", "owner", "updated_at"])
            )

        return FileStatus(
            operation_complete=True,
            **_unroll_object(f, key_map={"id": _format_id}, ignore=["owner"]),
        )


def fetch_file(file_id: str, chunk: int = None, verify: bool = False):
    """
    Fetches file information.

    Parameters:
        file_id: The id of the file to fetch.
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


def create_chunk(file_id: str, offset: int, data: str, upsert: bool = False, **kwargs):
    """
    Creates a chunk associated with a file.

    Parameters:
        file_id: The id of the file to associate the chunk with.
        offset: The chunk's offset index.
        data: The chunk's data.
        upsert: Flag to create a top-level file document if one doesn't exist.
    """
    return _save_chunk(file_id, offset=offset, data=data, upsert=upsert, **kwargs)


def delete_file(file_id: str):
    """
    Deletes a file and its chunks.

    Parameters:
        file_id: The id of the file.
    """
    file = check_file(file_id)
    # This should delete the associated chunks as well.
    db.delete(file)
    return FileStatus(operation_complete=True, **_format_id({}, file_id))


def set_owner(file_id: str, owner_id: str = None, owner_type: str = None):
    """
    Sets the owner field of the file.  This is used for DB pruning.

    Parameters:
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
            file.owner_type in OWNERSHIP_PRIORITY and file.owner is None
        ):
            if owner_type in OWNERSHIP_MAP:
                owner = db.query_unique(OWNERSHIP_MAP[owner_type], id=owner_id)
                file = db.modify(
                    file,
                    owner_id=owner_id,
                    owner_type=owner_type,
                    owner=owner.id if owner is not None else None,
                )
            else:
                file = db.modify(file, owner_id=owner_id, owner_type=owner_type)
            return FileStatus(
                operation_complete=True,
                **_unroll_object(file, key_map={"id": _format_id}, ignore=["owner"]),
            )
        return FileStatus(
            operation_complete=False,
            message=f"Owner type {owner_type} has lower priority than {file.owner_type}",
        )
    return FileStatus(
        operation_complete=False,
        message=f"Operation FILE_OWN requires an owner type "
        f"and id. Got {owner_type} and {owner_id}",
    )


def _check_file_ids(parameter, ids=None):
    """Used to scan operations for the FileID prefix.
    Parameters:
        parameter: The object to be scanned.
        ids: The current list of discovered file ids
    Returns:
        A list of file ids (may be empty).
    """
    if ids is None:
        ids = []
    if isinstance(parameter, six.string_types):
        if UI_FILE_ID_PREFIX in parameter:
            try:
                tmp_list = parameter.split(" ")
                prefix_idx = parameter.index(UI_FILE_ID_PREFIX)
                ids.append(tmp_list[prefix_idx + 1])
            except (IndexError, ValueError):
                pass

    elif isinstance(parameter, dict):
        for v in parameter.values():
            try:
                ids = _check_file_ids(v, ids)
            except (ReferenceError, IndexError):
                pass

    elif isinstance(parameter, list):
        for item in parameter:
            try:
                ids = _check_file_ids(item, ids)
            except IndexError:
                pass
    return ids


def set_owner_for_files(owner_id, owner_type, parameters):
    """ Scans the parameters for file ids, and sets ownership metadata."""
    for id in _check_file_ids(parameters):
        set_owner(id, owner_id=owner_id, owner_type=owner_type)


def forward_file(operation: Operation):
    """ Send file data before forwarding an operation with a file parameter. """
    ids = _check_file_ids(operation.model.parameters)
    for id in ids:
        file = check_chunks(id)
        args = [file.file_name, file.file_size, file.chunk_size]
        # Make sure we get all of the other data
        kwargs = dict(
            {"file_id": file.id, "upsert": True},
            # updated_at is a datetime field that can't be serialized, and owner
            # is a LazyReference field that causes crashing when being pushed forward.
            **_unroll_object(
                file,
                ignore=[
                    "file_name",
                    "file_size",
                    "chunk_size",
                    "id",
                    "updated_at",
                    "owner",
                ],
            ),
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
            # Just in case there's more data to include.
            c_kwargs = dict(
                {"upsert": True},
                # Owner is a LazyReference field that causes crashing when being pushed forward.
                **_unroll_object(chunk, ignore=["file_id", "offset", "data", "owner"]),
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


def handle_event(event):
    """Handle events"""
    if event.garden == config.get("garden.name"):
        if event.name == Events.JOB_CREATED.name:
            set_owner_for_files(
                event.payload.id, "JOB", event.payload.request_template.parameters
            )

        if event.name == Events.REQUEST_CREATED.name:
            set_owner_for_files(event.payload.id, "REQUEST", event.payload.parameters)
