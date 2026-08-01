"""Input validation for adversarial (AI-agent) input."""

from __future__ import annotations

from urllib.parse import quote

from mgs.errors import ValidationError


def encode_path_segment(value: str) -> str:
    """Percent-encode a value for safe embedding in a URL path segment.

    `safe=""` ensures `/`, `?`, `#`, spaces, and other reserved characters are encoded.
    """
    return quote(value, safe="")


def validate_resource_name(value: str) -> str:
    """Validate an id/UPN/resource name embedded in a URL path. Rejects traversal,
    control characters, and the URL-structural characters `?`, `#`, and backslash."""
    if not value:
        raise ValidationError("resource name must not be empty")
    if any(seg == ".." for seg in value.split("/")) or "..\\" in value:
        raise ValidationError(f"resource name contains path traversal: {value!r}")
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in value):
        raise ValidationError("resource name contains control characters")
    if any(c in value for c in "?#\\"):
        raise ValidationError(f"resource name contains invalid character: {value!r}")
    return value
