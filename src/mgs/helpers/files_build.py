"""Pure builders for file upload (remote path, chunking, session body)."""

from __future__ import annotations

import os

from mgs.drivepath import encode_drive_path

SMALL_MAX = 4 * 1024 * 1024
CHUNK_UNIT = 327680  # 320 KiB — Graph requires chunk sizes to be a multiple of this


def resolve_remote_path(local: str, to: str | None, name: str | None) -> str:
    fname = name or os.path.basename(local)
    if not to or to == "/":
        return "/" + fname
    dest = to if to.startswith("/") else "/" + to
    last = dest.rstrip("/").split("/")[-1]
    is_folder = dest.endswith("/") or "." not in last
    if is_folder:
        return dest.rstrip("/") + "/" + fname
    return dest


def upload_content_path(remote_path: str) -> str:
    return f"/me/drive/root:{encode_drive_path(remote_path)}:/content"


def upload_session_path(remote_path: str) -> str:
    return f"/me/drive/root:{encode_drive_path(remote_path)}:/createUploadSession"


def is_small(size: int) -> bool:
    return size <= SMALL_MAX


def normalize_chunk_size(mb: int) -> int:
    raw = max(int(mb), 0) * 1024 * 1024
    return max((raw // CHUNK_UNIT) * CHUNK_UNIT, CHUNK_UNIT)


def compute_chunks(total: int, chunk_size: int) -> list[tuple[int, int]]:
    out = []
    start = 0
    while start < total:
        end = min(start + chunk_size, total) - 1
        out.append((start, end))
        start = end + 1
    return out


def session_body() -> dict:
    return {"item": {"@microsoft.graph.conflictBehavior": "replace"}}
