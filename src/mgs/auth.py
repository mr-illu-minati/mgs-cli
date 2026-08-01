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
    "User.Read",
    "User.ReadBasic.All",
    "Mail.ReadWrite",
    "Mail.Send",
    "Calendars.ReadWrite",
    "Files.ReadWrite.All",
    "Team.ReadBasic.All",
    "Channel.ReadBasic.All",
    "ChannelMessage.Send",
    "Chat.ReadWrite",
    "Notes.ReadWrite",
]
SKEW_SECS = 60

GRAPH_RESOURCE = "https://graph.microsoft.com"
GRAPH_DEFAULT_SCOPE = "https://graph.microsoft.com/.default"
_NON_TENANT = {"common", "organizations", "consumers"}


def _now() -> int:
    return int(time.time())


def is_expired(expires_at: int) -> bool:
    return _now() + SKEW_SECS >= expires_at


def _effective_scopes() -> list[str]:
    """Scopes to request: the MGS_SCOPES override if set, else the full default set."""
    return config.resolve_scopes() or SCOPES


def _cert_thumbprint(pem: str) -> str:
    """SHA-1 hex thumbprint of the first CERTIFICATE block in a PEM (msal's expected format)."""
    import base64
    import hashlib
    import re

    m = re.search(r"-----BEGIN CERTIFICATE-----(.+?)-----END CERTIFICATE-----", pem, re.S)
    if not m:
        raise AuthError("certificate file contains no CERTIFICATE block")
    der = base64.b64decode("".join(m.group(1).split()))
    return hashlib.sha1(der).hexdigest()


def _client_credential():
    """msal client_credential for a secret (str) or certificate (dict), or None if neither is set."""
    secret = config.resolve_client_secret()
    if secret:
        return secret
    cert_path = config.resolve_cert_path()
    if cert_path:
        pem = Path(cert_path).read_text()
        return {"private_key": pem, "thumbprint": _cert_thumbprint(pem)}
    return None


def _confidential_token(client_credential) -> dict:
    """Acquire an app-only token via client credentials (secret / cert / client_assertion)."""
    import msal

    tenant = config.resolve_tenant()
    if tenant in _NON_TENANT:
        raise AuthError(
            "app-only auth requires a specific tenant; set MGS_TENANT_ID or "
            "AZURE_TENANT_ID to your tenant id or domain"
        )
    app = msal.ConfidentialClientApplication(
        config.resolve_client_id(),
        authority=f"https://login.microsoftonline.com/{tenant}",
        client_credential=client_credential,
    )
    return app.acquire_token_for_client(scopes=[GRAPH_DEFAULT_SCOPE])


def _secret_token(optional: bool = False) -> dict | None:
    cred = _client_credential()
    if cred is None:
        if optional:
            return None
        raise AuthError(
            "no client secret or certificate found; set AZURE_CLIENT_SECRET "
            "(or MGS_CLIENT_SECRET) or AZURE_CLIENT_CERTIFICATE_PATH"
        )
    return _confidential_token(cred)


def _workload_token(optional: bool = False) -> dict | None:
    fed = config.resolve_federated_token_file()
    if not fed:
        if optional:
            return None
        raise AuthError("workload identity federation requires AZURE_FEDERATED_TOKEN_FILE")
    assertion = Path(fed).read_text().strip()
    return _confidential_token({"client_assertion": assertion})


def _mi_token(optional: bool = False) -> dict | None:
    import msal
    import requests

    mi_client_id = config.resolve_explicit_client_id()
    identity = (
        msal.UserAssignedManagedIdentity(client_id=mi_client_id)
        if mi_client_id
        else msal.SystemAssignedManagedIdentity()
    )
    client = msal.ManagedIdentityClient(identity, http_client=requests.Session())
    return client.acquire_token_for_client(resource=GRAPH_RESOURCE)


def _acquire_app_only(config_dir: str, mode: str) -> str:
    """App-only token: pinned mechanism, or the full chain for mode 'app-only'."""
    if mode == "secret":
        result = _secret_token(optional=False)
    elif mode == "workload":
        result = _workload_token(optional=False)
    elif mode == "managed-identity":
        result = _mi_token(optional=False)
    else:  # "app-only": secret/cert -> workload federation -> managed identity
        result = (
            _secret_token(optional=True)
            or _workload_token(optional=True)
            or _mi_token(optional=True)
        )

    if not result or "access_token" not in result:
        detail = (result or {}).get("error_description") if result else None
        raise AuthError(detail or f"app-only auth failed (MGS_AUTH={mode})")

    expires_at = _now() + int(result.get("expires_in", 3600))
    _write_fast(config_dir, result["access_token"], expires_at)
    return result["access_token"]


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
    mode = config.resolve_auth_mode()
    if mode != "delegated":
        return _acquire_app_only(config_dir, mode)
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
    """Force a fresh login. Delegated: interactive/device. App-only: a non-interactive credential check."""
    mode = config.resolve_auth_mode()
    if mode != "delegated":
        return _acquire_app_only(config_dir, mode)
    return _acquire_via_msal(config_dir, force_interactive=True)


def logout(config_dir: str) -> None:
    for name in ("token.json", "msal_cache.json"):
        try:
            (Path(config_dir) / name).unlink()
        except OSError:
            pass
