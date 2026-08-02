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


def resolve_scopes() -> list[str] | None:
    """Delegated Graph scopes from MGS_SCOPES (space/comma-separated), or None for defaults."""
    raw = _env("MGS_SCOPES")
    if not raw:
        return None
    return [s for s in raw.replace(",", " ").split() if s]


def resolve_client_secret() -> str | None:
    return _env("AZURE_CLIENT_SECRET") or _env("MGS_CLIENT_SECRET")


def resolve_cert_path() -> str | None:
    return _env("AZURE_CLIENT_CERTIFICATE_PATH") or _env("MGS_CLIENT_CERTIFICATE_PATH")


def resolve_federated_token_file() -> str | None:
    return _env("AZURE_FEDERATED_TOKEN_FILE")


def resolve_explicit_client_id() -> str | None:
    """Client id only if explicitly set (no builtin fallback) — for user-assigned managed identity."""
    return _env("MGS_CLIENT_ID") or _env("AZURE_CLIENT_ID")


AUTH_MODES = ("delegated", "app-only", "secret", "workload", "managed-identity")
_AUTH_ALIASES = {"msi": "managed-identity", "interactive": "delegated"}


def _ambient_app_only() -> bool:
    """True when app-only credentials are detectably present (checked only when MGS_AUTH is unset)."""
    if resolve_client_secret() or resolve_cert_path() or resolve_federated_token_file():
        return True
    # Env-based managed-identity endpoints (App Service / Functions / Container Apps / Arc / Cloud Shell).
    # Plain-IMDS VMs expose no env var — those require explicit MGS_AUTH=managed-identity.
    return bool(_env("IDENTITY_ENDPOINT") or _env("MSI_ENDPOINT"))


def resolve_auth_mode() -> str:
    """One of AUTH_MODES. Unset MGS_AUTH → 'delegated', or 'app-only' when ambient creds are present."""
    raw = _env("MGS_AUTH")
    if not raw:
        return "app-only" if _ambient_app_only() else "delegated"
    mode = raw.strip().lower()
    mode = _AUTH_ALIASES.get(mode, mode)
    if mode not in AUTH_MODES:
        from mgs.errors import UsageError

        raise UsageError(f"invalid MGS_AUTH={raw!r}; expected one of: {', '.join(AUTH_MODES)}")
    return mode


# Mailbox targeted by /me/-style paths, set from the --mailbox CLI flag.
_mailbox_override: str | None = None


def set_mailbox(value: str | None) -> None:
    global _mailbox_override
    _mailbox_override = value


def resolve_mailbox() -> str | None:
    """Target mailbox UPN: --mailbox flag > MGS_MAILBOX > MGS_DEFAULT_MAILBOX (app-only only)."""
    if _mailbox_override:
        return _mailbox_override
    env = _env("MGS_MAILBOX")
    if env:
        return env
    if resolve_auth_mode() != "delegated":
        return _env("MGS_DEFAULT_MAILBOX")
    return None


def config_dir() -> Path:
    override = _env("MGS_CONFIG_DIR")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "mgs"
