"""mgs auth: login / logout / status (all emit JSON-able dicts)."""

from __future__ import annotations

from mgs import auth, config
from mgs.errors import UsageError


def status_value(config_dir: str) -> dict:
    mode = config.resolve_auth_mode()
    fast = auth._read_fast(config_dir)
    if fast and not auth.is_expired(fast["expires_at"]):
        return {"authenticated": True, "mode": mode, "expires_at": fast["expires_at"]}
    return {"authenticated": False, "mode": mode}


def run(action: str, config_dir: str) -> dict:
    if action == "login":
        auth.login(config_dir)
        return status_value(config_dir)
    if action == "logout":
        auth.logout(config_dir)
        return {"authenticated": False, "loggedOut": True}
    if action == "status":
        return status_value(config_dir)
    raise UsageError(f"unknown auth action: {action}")
