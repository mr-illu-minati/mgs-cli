"""Config dir + MGS_/AZURE_ env resolution."""

from __future__ import annotations

import os
from pathlib import Path

# mgs's own multi-tenant public-client app ("mgs CLI"), registered in Entra ID. It is a
# public client (no secret), registers the http://localhost loopback redirect, and requests
# delegated Microsoft Graph scopes (see auth.SCOPES). Sign-ins show as "mgs CLI" in tenant
# audit logs. Bring your own app by setting MGS_CLIENT_ID. See docs/auth-production.md.
BUILTIN_CLIENT_ID = "59b3a13e-fefb-4ded-872f-143ea9bfce27"


def _env(key: str) -> str | None:
    val = os.environ.get(key)
    return val if val else None


def resolve_client_id() -> str:
    return _env("MGS_CLIENT_ID") or _env("AZURE_CLIENT_ID") or BUILTIN_CLIENT_ID


def resolve_tenant() -> str:
    return _env("MGS_TENANT_ID") or _env("AZURE_TENANT_ID") or "common"


def config_dir() -> Path:
    override = _env("MGS_CONFIG_DIR")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "mgs"
