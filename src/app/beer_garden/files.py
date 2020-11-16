# -*- coding: utf-8 -*-
from math import ceil
from bson import ObjectId
from bson.errors import InvalidId
from json import dumps
from datetime import datetime

import beer_garden.db.api as db
from beer_garden.errors import NotUniqueException
from brewtils.errors import ModelValidationError, NotFoundError
from brewtils.models import File, FileChunk, Request, Job
from brewtils.resolvers.parameter import UI_FILE_ID_PREFIX


# 15MB
MAX_CHUNK_SIZE = 1024 * 1024 * 15
OWNERSHIP_PRIORITY = {
    "JOB": 1,
    "REQUEST": 2,
}


def check_file(file_id: str, upsert: bool = False):
    """
    Checks that the file with file_id exists in the DB.

    Parameters:
        file_id: The id for the requested file.
        upsert: (Optional) If the file doesn't exist, create a placeholder file to be modified later.

    Returns:
        The file object.

    Raises:
        NotFoundError: Raised when a file with the requested ID doesn't exist and is expected to.
        ModelValidationError: Raised when an ID is provided, but is of the incorrect format.
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
            return db.query_unique(File, id=file_id)
        else:
            raise NotFoundError(f"Tried to fetch an unsaved file {file_id}.")
    return res


def check_chunk(chunk_id: str):
    """
    Checks that the file with file_id exists in the DB.

    Parameters:
        chunk_id: The id for the requested chunk.

    Returns:
        The file object.

    Raises:
        NotFoundError: Raised when a chunk with the requested ID doesn't exist.
        ModelValidationError: Raised when an ID is provided, but is of the incorrect format.
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

    res = db.query_unique(FileChunk, id=chunk_id)
    if res is None:
        raise NotFoundError(f"Tried to fetch an unsaved chunk {chunk_id}.")
    return res


def check_chunks(file_id: str):
    """
    Checks that the file with file_id has a valid chunks field.

    Parameters:
        file_id: This should be a valid file id.

    Returns:
        The wrapped function.

    Raises:
        NotFoundError: Raised when a file with the requested ID doesn't exist and is expected to.
        ModelValidationError: Raised when a file with the requested ID doesn't have any associate file chunks.
    """
    res = check_file(file_id)
    if res.chunks is None:
        raise ModelValidationError(
            f"Tried to load a file {res.id} with no associated chunks."
        )
    return res


def _save_chunk(file_id: str, offset: int = None, upsert: bool = False, **kwargs):
    """
    Saves the provided chunk data to the DB and updates
    the parent document with the chunk id.

    Parameters:
        file: This should be a valid file id.
        n: The offset index. (e.g. 0, 1, 2, ...)
        kwargs: The other parameters for FileChunk that we don't need to check)

    Raises:
        NotFoundError: Raised when a file with the requested ID doesn't exist and is expected to.
    """
    file = check_file(file_id, upsert=upsert)
    chunk = FileChunk(file_id=file.id, offset=offset, **kwargs)
    c = db.create(chunk)
    # This is starting to get DB-specific, but we want to be sure this is an atomic operation.
    modify = {f"set__chunks__{offset}": c.id}
    db.modify(file, **modify)
    db.modify(c, owner=file.id)
    return dumps({"id": c.id})


def _verify_chunks(file_id: str):
    """
    Processes the requested file to determine if any chunks are missing.

    Parameters:
        file_id: This should be a valid file id.

    Returns:
        A dictionary that describes the validity of the file.

    Raises:
        NotFoundError: Raised when a file with the requested ID doesn't exist and is expected to.
        ModelValidationError: Raised when a file with the requested ID doesn't have any associate file chunks.
    """
    file = check_chunks(file_id)
    num_chunks = ceil(file.file_size / file.chunk_size)
    computed_size = file.chunk_size * num_chunks

    size_ok = file.file_size <= computed_size
    length_ok = num_chunks == len(file.chunks)

    missing = [
        x for x in range(len(file.chunks)) if file.chunks.get(str(x), None) is None
    ]
    return {
        "valid": (length_ok and missing == [] and size_ok),
        "missing": missing,
        "expected_max_size": computed_size,
        "file_size": file.file_size,
        "size_ok": size_ok,
        "expected_number_of_chunks": num_chunks,
        "number_of_chunks": len(file.chunks),
        "file_chunks": file.chunks,
        "length_ok": length_ok,
    }


def _fetch_chunk(file_id: str, chunk_num: int):
    """
    Fetches a single chunk of the requested file.

    Parameters:
        file_id: This should be a valid file id.
        chunk_num: The offset index. (e.g. 0, 1, 2, ..)

    Returns:
        The chunk data.

    Raises:
        NotFoundError: Raised when a file with the requested ID doesn't exist and is expected to.
        ModelValidationError: Raised when a file with the requested ID doesn't have any associate file chunks.
        ValueError: Raised when the chunk number requested is not associated with the given file.
    """
    file = check_chunks(file_id)
    if str(chunk_num) in file.chunks:
        chunk = check_chunk(file.chunks[str(chunk_num)])
        return chunk.data
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
        NotFoundError: Raised when a file with the requested ID doesn't exist and is expected to.
        ModelValidationError: Raised when a file with the requested ID doesn't have any associate file chunks.
    """
    # This is going to get big, try our best to be efficient
    check = _verify_chunks(file_id)
    if check["valid"]:
        file = check_chunks(file_id)
        all_data = [
            db.query_unique(FileChunk, id=file.chunks[str(x)]).data
            for x in range(len(file.chunks))
        ]
        return "".join(all_data)
    else:
        return None


def _delete_file(file_id: str):
    """
    Deletes the requested file and its corresponding chunks.

    Parameters:
        file_id: This should be a valid file id.

    Raises:
        NotFoundError: Raised when a file with the requested ID doesn't exist and is expected to.
    """
    file = check_file(file_id)
    # This should delete the associated chunks as well.
    db.delete(file)
    return dumps({"done": True})


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
        ModelValidationError: Raised when a file id (if provided) is not a valid ObjectId string.
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
        created_at=datetime.utcnow(),
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

    # Safe creation process, handles out-of-order file uploads but may
    # combine existing data with collision
    else:
        res = db.query_unique(File, id=f.id)
        if res is None:
            f = db.create(f)
        else:
            db.modify(
                f, file_name=file_name, file_size=file_size, chunk_size=chunk_size
            )
            f = db.query_unique(File, id=f.id)

    return dumps(
        {
            "id": f"{UI_FILE_ID_PREFIX} {f.id}",
            "name": f.file_name,
            "size": f.file_size,
            "chunk_size": f.chunk_size,
        }
    )


def fetch_file(file_id: str, chunk: int = None, verify: bool = False):
    """
    Fetches file information.

    Parameters:
        file_id: The id of the file to fetch.
        chunk: (Optional) If included, fetches a single chunk instead of the entire file.
        verify: (Optional) If included, fetches file validity information instead of data.

    Returns:
        The requested information, unless an error occurs. (Actual contents determined by optional flags)
    """
    if verify:
        try:
            return dumps(_verify_chunks(file_id))
        except (ModelValidationError, NotFoundError):
            return None

    if chunk is not None:
        try:
            return _fetch_chunk(file_id, chunk)
        except (ModelValidationError, ValueError, NotFoundError):
            return None

    else:
        try:
            return _fetch_file(file_id)
        except (ModelValidationError, NotFoundError):
            return None


def create_chunk(file_id: str, offset: int, data: str, upsert: bool = False):
    """
    Creates a chunk associated with a file.

    Parameters:
        file_id: The id of the file to associate the chunk with.
        offset: The chunk's offset index.
        data: The chunk's data.
    """
    try:
        return _save_chunk(file_id, offset=offset, data=data, upsert=upsert)
    except (NotFoundError, ModelValidationError):
        return None


def delete_file(file_id: str):
    """
    Deletes a file and its chunks.

    Parameters:
        file_id: The id of the file.
    """
    try:
        return _delete_file(file_id)
    except (NotFoundError, ModelValidationError):
        return None


def set_owner(file_id: str, owner_id: str = None, owner_type: str = None):

    """
    Sets the owner field of the file.  This is used for DB pruning.

    Parameters:
        file_id: The id of the file.
        owner_id: The id of the owner.
        owner_type: The type of the owner (job/request).
    """
    if (owner_id is not None) and (owner_type is not None):
        try:
            file = check_chunks(file_id)
            # Job owners should override request owners (if one is already set)
            if file.owner_type is None or OWNERSHIP_PRIORITY.get(
                owner_type, 1_000_000
            ) <= OWNERSHIP_PRIORITY.get(file.owner_type, 1_000_000):
                if owner_type == "REQUEST":
                    owner = db.query_unique(Request, id=owner_id)
                elif owner_type == "JOB":
                    owner = db.query_unique(Job, id=owner_id)
                else:
                    owner = None
                db.modify(file, owner_id=owner_id, owner_type=owner_type, owner=owner)
                return dumps({"done": True})

            return None
        except (ModelValidationError, NotFoundError):
            return None
