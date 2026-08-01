"""OneDrive/SharePoint drive-item path addressing (by id or by /path)."""

from __future__ import annotations

from urllib.parse import quote

from mgs.errors import ValidationError


def is_path_ref(ref: str) -> bool:
    return ref.startswith("/")


def encode_drive_path(path: str) -> str:
    """Percent-encode each path segment, preserving slashes. Rejects `..` traversal."""
    segments = path.split("/")
    if any(seg == ".." for seg in segments):
        raise ValidationError(f"path contains traversal: {path!r}")
    return "/".join(quote(seg, safe="") if seg else "" for seg in segments)


def drive_item_base(ref: str) -> str:
    """Base Graph path to address a drive item by `/path` or by id."""
    if is_path_ref(ref):
        return f"/me/drive/root:{encode_drive_path(ref)}:"
    from mgs.validate import encode_path_segment, validate_resource_name

    validate_resource_name(ref)
    return f"/me/drive/items/{encode_path_segment(ref)}"
