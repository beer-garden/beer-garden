# -*- coding: utf-8 -*-
from math import ceil
from bson import ObjectId
from bson.errors import InvalidId
from json import dumps

import beer_garden.db.api as db
from beer_garden.errors import NotUniqueException
from brewtils.errors import ModelValidationError
from brewtils.models import File, FileChunk


# 10MB
MAX_CHUNK_SIZE = 1024 * 1024 * 10
UI_FILE_ID_PREFIX = "BGFileID:"


def check_file(file_id: str, upsert: bool = False):
    """
    Wrapper that checks that the file with file_id exists in the DB.

    Parameters:
        file_id: The id for the requested file.

    Returns:
        The file object.
    """
    res = db.query_unique(File, id=file_id)
    if res is None:
        if upsert:
            print(f"~~~~~~~~~~~~~Creating a placeholder file for id {file_id}")
            create_file("BG_placeholder", 0, 0, file_id)
            return db.query_unique(File, id=file_id)
        else:
            raise ModelValidationError(f"Tried to fetch an unsaved file {file_id}.")
    return res


def check_chunk(chunk_id: str):
    """
    Wrapper that checks that the file with file_id exists in the DB.

    Parameters:
        chunk_id: The id for the requested chunk.

    Returns:
        The file object.
    """
    res = db.query_unique(FileChunk, id=chunk_id)
    if res is None:
        raise ModelValidationError(f"Tried to fetch an unsaved chunk {chunk_id}.")
    return res


def check_chunks(file_id: str):
    """
    Wrapper that checks that the file with file_id has a valid chunks field.

    Parameters:
        file_id: This should be a valid file id.

    Returns:
        The wrapped function.
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
    """
    file = check_file(file_id, upsert=upsert)
    chunk = FileChunk(file_id=file.id, offset=offset, **kwargs)
    c = db.create(chunk)
    modify = {f"set__chunks__{offset}": c.id}
    db.modify(file, **modify)
    return dumps({"id": c.id})


def _verify_chunks(file_id: str):
    """
    Processes the requested file to determine if any chunks are missing.

    Parameters:
        file_id: This should be a valid file id.

    Returns:
        A dictionary that describes the validity of the file.
    """
    file = check_chunks(file_id)
    num_chunks = ceil(file.file_size / file.chunk_size)
    computed_size = file.chunk_size * num_chunks

    length_ok = num_chunks == len(file.chunks)
    size_ok = file.file_size <= computed_size <= file.file_size + file.chunk_size

    missing = [
        x for x in range(len(file.chunks)) if file.chunks.get(str(x), None) is None
    ]
    return {"valid": (length_ok and missing == [] and size_ok), "missing": missing}


def _fetch_chunk(file_id: str, chunk_num: str):
    """
    Fetches a single chunk of the requested file.

    Parameters:
        file_id: This should be a valid file id.
        chunk_num: The offset index. (e.g. 0, 1, 2, ..)

    Returns:
        The chunk data.
    """
    file = check_chunks(file_id)
    if chunk_num in file.chunks:
        chunk = check_chunk(file.chunks[chunk_num])
        return chunk.data
    else:
        raise ValueError(f"Chunk number {chunk_num} is invalid for file {file.id}")


def _fetch_file(file_id: str):
    """
    Fetches the entire requested file.

    Parameters:
        file_id: This should be a valid file id.

    Returns:
        The file data.
    """
    file = check_chunks(file_id)
    # This is going to get big, try our best to be efficient
    all_data = [
        db.query_unique(FileChunk, id=file.chunks[str(x)]).data
        for x in range(len(file.chunks))
    ]
    return "".join(all_data)


def _delete_file(file_id: str):
    """
    Deletes the requested file and its corresponding chunks.

    Parameters:
        file_id: This should be a valid file id.
    """
    file = check_chunks(file_id)
    # Get rid of all of the chunks first
    for chunk_id in file.chunks.values():
        try:
            chunk = check_chunk(chunk_id)
            db.delete(chunk)
        except ModelValidationError:
            pass
    # Delete the parent file object
    db.delete(file)
    return dumps({"done": True})


def create_file(
    file_name: str,
    file_size: int,
    chunk_size: int,
    file_id: ObjectId = None,
    upsert: bool = False,
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

    Returns:
        A dictionary with the id.
    """
    if chunk_size > MAX_CHUNK_SIZE:
        raise ValueError(
            f"Cannot create a file with chunk size greater than {MAX_CHUNK_SIZE}."
        )

    f = File(file_name=file_name, file_size=file_size, chunk_size=chunk_size)

    # Override the file id if passed in
    if file_id is not None:
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
            "id": f.id,
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
        The requested information. (Actual contents determined by optional flags)
    """
    if verify:
        return dumps(_verify_chunks(file_id))
    if chunk is not None:
        return _fetch_chunk(file_id, chunk)
    else:
        return _fetch_file(file_id)


def create_chunk(file_id: str, offset: int, data: str, upsert: bool = False):
    """
    Creates a chunk associated with a file.

    Parameters:
        file_id: The id of the file to associate the chunk with.
        offset: The chunk's offset index.
        data: The chunk's data.
    """
    return _save_chunk(file_id, offset=offset, data=data, upsert=upsert)


def delete_file(file_id: str):
    """
    Deletes a file and its chunks.

    Parameters:
        file_id: The id of the file.
    """
    return _delete_file(file_id)
