"""Token acquisition: MGS_TOKEN > valid fast-path cache > MSAL (silent/interactive/device)."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from mgs import config
from mgs.errors import AuthError

SCOPES = [
    "User.Read", "User.ReadBasic.All", "Mail.ReadWrite", "Mail.Send", "Calendars.ReadWrite",
    "Files.ReadWrite.All", "Team.ReadBasic.All", "Channel.ReadBasic.All", "ChannelMessage.Send",
    "Chat.ReadWrite", "Notes.ReadWrite",
]
SKEW_SECS = 60


def _now() -> int:
    return int(time.time())


def is_expired(expires_at: int) -> bool:
    return _now() + SKEW_SECS >= expires_at


def _effective_scopes() -> list[str]:
    """Scopes to request: the MGS_SCOPES override if set, else the full default set."""
    return config.resolve_scopes() or SCOPES


def _token_path(config_dir: str) -> Path:
    return Path(config_dir) / "token.json"


def _read_fast(config_dir: str) -> dict | None:
    try:
        return json.loads(_token_path(config_dir).read_text())
    except (OSError, ValueError):
        return None


def _write_fast(config_dir: str, access_token: str, expires_at: int) -> None:
    p = _token_path(config_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"access_token": access_token, "expires_at": expires_at}))
    os.chmod(p, 0o600)


def get_token(config_dir: str) -> str:
    """Return a usable Graph access token, importing MSAL only if a fresh token is needed."""
    env_tok = os.environ.get("MGS_TOKEN")
    if env_tok:
        return env_tok
    fast = _read_fast(config_dir)
    if fast and not is_expired(fast["expires_at"]):
        return fast["access_token"]
    return _acquire_via_msal(config_dir, force_interactive=False)


def _acquire_via_msal(config_dir: str, force_interactive: bool) -> str:
    import msal  # lazy: never imported on the valid-cache fast path

    cache = msal.SerializableTokenCache()
    cache_path = Path(config_dir) / "msal_cache.json"
    if cache_path.exists():
        cache.deserialize(cache_path.read_text())

    app = msal.PublicClientApplication(
        config.resolve_client_id(),
        authority=f"https://login.microsoftonline.com/{config.resolve_tenant()}",
        token_cache=cache,
    )

    scopes = _effective_scopes()
    result = None
    if not force_interactive:
        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(scopes, account=accounts[0])

    if not result:
        if os.environ.get("MGS_NO_BROWSER"):
            flow = app.initiate_device_flow(scopes=scopes)
            print(flow.get("message", "Complete device-code sign-in."), file=sys.stderr)
            result = app.acquire_token_by_device_flow(flow)
        else:
            result = app.acquire_token_interactive(scopes=scopes)

    if not result or "access_token" not in result:
        detail = (result or {}).get("error_description", "interactive login failed")
        raise AuthError(detail)

    if cache.has_state_changed:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(cache.serialize())
        os.chmod(cache_path, 0o600)

    expires_at = _now() + int(result.get("expires_in", 3600))
    _write_fast(config_dir, result["access_token"], expires_at)
    return result["access_token"]


def login(config_dir: str) -> str:
    """Force an interactive (or device-code) login regardless of cache state."""
    return _acquire_via_msal(config_dir, force_interactive=True)


def logout(config_dir: str) -> None:
    for name in ("token.json", "msal_cache.json"):
        try:
            (Path(config_dir) / name).unlink()
        except OSError:
            pass
