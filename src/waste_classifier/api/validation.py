"""Shared input-validation helpers for upload-accepting endpoints.

Centralized here so /api/predict, /api/detect, and /api/transcribe enforce
identical size/type limits rather than each reimplementing (and potentially
drifting on) the same checks.
"""

from __future__ import annotations

import io

from fastapi import HTTPException, Request, UploadFile
from PIL import Image

from waste_classifier import config

_CHUNK_SIZE = 1024 * 1024  # 1 MB


def reject_oversized_content_length(request: Request) -> None:
    """Fast-path rejection using the Content-Length header, before reading
    any body at all. Best-effort only: a missing/lying header falls through
    to the chunked-read enforcement in read_upload_bounded()."""
    content_length = request.headers.get("content-length")
    if content_length is None:
        return
    try:
        declared = int(content_length)
    except ValueError:
        return
    if declared > config.MAX_UPLOAD_BYTES:
        limit_mb = config.MAX_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=413, detail=f"Request exceeds the {limit_mb}MB upload limit."
        )


def read_upload_bounded(upload_file: UploadFile) -> bytes:
    """Read an UploadFile's contents, aborting early once it exceeds the
    configured limit. Reads in fixed-size chunks with a running counter --
    never calls .read() unbounded -- so a client that omits or lies about
    Content-Length can't force an unbounded read into memory."""
    max_bytes = config.MAX_UPLOAD_BYTES
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = upload_file.file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file exceeds the {max_bytes // (1024 * 1024)}MB limit.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def validate_image_content_type(content_type: str | None) -> None:
    if content_type not in config.ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported content type '{content_type}'. "
                f"Allowed: {', '.join(sorted(config.ALLOWED_IMAGE_CONTENT_TYPES))}."
            ),
        )


def open_and_verify_image(contents: bytes) -> Image.Image:
    """Open and validate image bytes, guarding against decompression bombs
    and corrupt/non-image payloads. Image.verify() invalidates the file
    object for further use, so we reopen a fresh one to actually return."""
    try:
        probe = Image.open(io.BytesIO(contents))
        probe.verify()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.") from exc
    return Image.open(io.BytesIO(contents))
