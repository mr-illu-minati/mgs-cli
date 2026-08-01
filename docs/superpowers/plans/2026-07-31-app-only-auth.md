# App-only Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an unattended **app-only** auth track (client secret/cert → workload identity federation → managed identity) selectable and pinnable via `MGS_AUTH`, without adding any new dependency.

**Architecture:** A second token-acquisition track alongside today's delegated MSAL flow. `config.resolve_auth_mode()` decides the track from `MGS_AUTH` (with ambient auto-detection only when unset). `auth._acquire_app_only()` implements the chain and per-mechanism short-circuits using `msal.ConfidentialClientApplication` (secret/cert/`client_assertion`) and `msal.ManagedIdentityClient`. `MGS_TOKEN` and the fast-path cache sit above both tracks, unchanged.

**Tech Stack:** Python stdlib, `msal` (already a dependency; also transitively provides `requests`, used by `ManagedIdentityClient`). App-only requests the `https://graph.microsoft.com/.default` scope (application permissions).

---

## Background for the implementer

Read these before starting:
- Spec: `docs/superpowers/specs/2026-07-31-app-only-auth-design.md`
- `src/mgs/config.py` — env resolution (`_env`, `resolve_client_id`, `resolve_tenant`, `resolve_scopes`).
- `src/mgs/auth.py` — token acquisition (`get_token`, `_acquire_via_msal`, `_write_fast`, `_now`, `is_expired`, `login`, `logout`).
- `src/mgs/errors.py` — `AuthError` (exit 3), `UsageError` (exit 2).
- `src/mgs/auth_commands.py` — `status_value`, `run`.

Key facts:
- `msal` is imported **lazily** inside functions so the valid-cache fast path never imports it. Keep that pattern. App-only tests inject a fake `msal` module via `monkeypatch.setitem(sys.modules, "msal", fake)`.
- `config.resolve_client_id()` falls back to `BUILTIN_CLIENT_ID`. For **user-assigned managed identity** we must NOT use that fallback — a new `resolve_explicit_client_id()` returns the client id only if explicitly set.
- App-only requires a **real tenant** — `common`/`organizations`/`consumers` are invalid for client credentials.
- Run the whole suite with `uv run pytest -q` (150 tests pass today; keep them green).

---

## Task 1: Config readers for app-only credentials

**Files:**
- Modify: `src/mgs/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_config.py`:

```python
def test_resolve_client_secret_prefers_azure_then_mgs(monkeypatch):
    from mgs import config
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("MGS_CLIENT_SECRET", raising=False)
    assert config.resolve_client_secret() is None
    monkeypatch.setenv("MGS_CLIENT_SECRET", "mgs-sec")
    assert config.resolve_client_secret() == "mgs-sec"
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "az-sec")
    assert config.resolve_client_secret() == "az-sec"


def test_resolve_cert_path(monkeypatch):
    from mgs import config
    monkeypatch.delenv("AZURE_CLIENT_CERTIFICATE_PATH", raising=False)
    monkeypatch.delenv("MGS_CLIENT_CERTIFICATE_PATH", raising=False)
    assert config.resolve_cert_path() is None
    monkeypatch.setenv("MGS_CLIENT_CERTIFICATE_PATH", "/tmp/c.pem")
    assert config.resolve_cert_path() == "/tmp/c.pem"


def test_resolve_federated_token_file(monkeypatch):
    from mgs import config
    monkeypatch.delenv("AZURE_FEDERATED_TOKEN_FILE", raising=False)
    assert config.resolve_federated_token_file() is None
    monkeypatch.setenv("AZURE_FEDERATED_TOKEN_FILE", "/var/run/tok")
    assert config.resolve_federated_token_file() == "/var/run/tok"


def test_resolve_explicit_client_id_no_builtin_fallback(monkeypatch):
    from mgs import config
    monkeypatch.delenv("MGS_CLIENT_ID", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    assert config.resolve_explicit_client_id() is None  # NOT the builtin
    monkeypatch.setenv("AZURE_CLIENT_ID", "abc")
    assert config.resolve_explicit_client_id() == "abc"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config.py -k "client_secret or cert_path or federated or explicit_client" -v`
Expected: FAIL with `AttributeError: module 'mgs.config' has no attribute 'resolve_client_secret'`

- [ ] **Step 3: Implement the readers**

In `src/mgs/config.py`, add after `resolve_scopes()`:

```python
def resolve_client_secret() -> str | None:
    return _env("AZURE_CLIENT_SECRET") or _env("MGS_CLIENT_SECRET")


def resolve_cert_path() -> str | None:
    return _env("AZURE_CLIENT_CERTIFICATE_PATH") or _env("MGS_CLIENT_CERTIFICATE_PATH")


def resolve_federated_token_file() -> str | None:
    return _env("AZURE_FEDERATED_TOKEN_FILE")


def resolve_explicit_client_id() -> str | None:
    """Client id only if explicitly set (no builtin fallback) — for user-assigned managed identity."""
    return _env("MGS_CLIENT_ID") or _env("AZURE_CLIENT_ID")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py -k "client_secret or cert_path or federated or explicit_client" -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/mgs/config.py tests/test_config.py
git commit -m "feat(config): readers for app-only credentials (secret/cert/federated/explicit id)"
```

---

## Task 2: `resolve_auth_mode` + ambient detection

**Files:**
- Modify: `src/mgs/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_config.py`:

```python
import pytest
from mgs.errors import UsageError


def _clear_auth_env(monkeypatch):
    for k in ("MGS_AUTH", "AZURE_CLIENT_SECRET", "MGS_CLIENT_SECRET",
              "AZURE_CLIENT_CERTIFICATE_PATH", "MGS_CLIENT_CERTIFICATE_PATH",
              "AZURE_FEDERATED_TOKEN_FILE", "IDENTITY_ENDPOINT", "MSI_ENDPOINT"):
        monkeypatch.delenv(k, raising=False)


def test_auth_mode_defaults_to_delegated(monkeypatch):
    from mgs import config
    _clear_auth_env(monkeypatch)
    assert config.resolve_auth_mode() == "delegated"


def test_auth_mode_explicit_values_and_aliases(monkeypatch):
    from mgs import config
    _clear_auth_env(monkeypatch)
    for raw, expected in [("app-only", "app-only"), ("secret", "secret"),
                          ("workload", "workload"), ("managed-identity", "managed-identity"),
                          ("msi", "managed-identity"), ("MSI", "managed-identity"),
                          ("interactive", "delegated"), ("delegated", "delegated")]:
        monkeypatch.setenv("MGS_AUTH", raw)
        assert config.resolve_auth_mode() == expected


def test_auth_mode_unknown_raises_usage(monkeypatch):
    from mgs import config
    _clear_auth_env(monkeypatch)
    monkeypatch.setenv("MGS_AUTH", "bogus")
    with pytest.raises(UsageError):
        config.resolve_auth_mode()


def test_auth_mode_ambient_detection_only_when_unset(monkeypatch):
    from mgs import config
    _clear_auth_env(monkeypatch)
    # A secret present with MGS_AUTH unset flips to app-only.
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "sec")
    assert config.resolve_auth_mode() == "app-only"
    # Managed-identity endpoint env also flips it.
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("IDENTITY_ENDPOINT", "http://169.254.169.254/")
    assert config.resolve_auth_mode() == "app-only"
    # Explicit MGS_AUTH overrides ambient detection.
    monkeypatch.setenv("MGS_AUTH", "delegated")
    assert config.resolve_auth_mode() == "delegated"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config.py -k auth_mode -v`
Expected: FAIL with `AttributeError: module 'mgs.config' has no attribute 'resolve_auth_mode'`

- [ ] **Step 3: Implement `resolve_auth_mode` + `_ambient_app_only`**

In `src/mgs/config.py`, add (top-level constant near the top, functions after the readers from Task 1). Add the import at the top of the file if not present: `from mgs.errors import UsageError` — but to avoid a circular import, import it lazily inside the function instead.

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py -k auth_mode -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/mgs/config.py tests/test_config.py
git commit -m "feat(config): resolve_auth_mode with MGS_AUTH selection + ambient app-only detection"
```

---

## Task 3: App-only helpers — confidential-client token + credential builder

**Files:**
- Modify: `src/mgs/auth.py`
- Test: `tests/test_auth_app_only.py` (new)

This task adds the shared pieces used by every app-only mechanism: constants, the certificate-thumbprint helper (stdlib only), the client-credential builder, and `_confidential_token`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_auth_app_only.py`:

```python
import sys
import types
import pytest
from mgs.errors import AuthError


def _fake_msal(monkeypatch):
    """Inject a fake msal module; return a dict capturing constructor args."""
    captured = {}

    class FakeConfidential:
        def __init__(self, client_id, authority=None, client_credential=None):
            captured["confidential"] = {
                "client_id": client_id, "authority": authority, "cred": client_credential,
            }

        def acquire_token_for_client(self, scopes=None):
            captured["scopes"] = scopes
            return {"access_token": "app-tok", "expires_in": 3600}

    fake = types.ModuleType("msal")
    fake.ConfidentialClientApplication = FakeConfidential
    monkeypatch.setitem(sys.modules, "msal", fake)
    return captured


def test_confidential_token_builds_client_and_requests_default_scope(monkeypatch):
    from mgs import auth
    captured = _fake_msal(monkeypatch)
    monkeypatch.setenv("MGS_TENANT_ID", "contoso.onmicrosoft.com")
    monkeypatch.setenv("MGS_CLIENT_ID", "the-client")
    result = auth._confidential_token("a-secret")
    assert result["access_token"] == "app-tok"
    assert captured["scopes"] == ["https://graph.microsoft.com/.default"]
    assert captured["confidential"]["cred"] == "a-secret"
    assert captured["confidential"]["authority"].endswith("/contoso.onmicrosoft.com")


def test_confidential_token_rejects_common_tenant(monkeypatch):
    from mgs import auth
    _fake_msal(monkeypatch)
    monkeypatch.setenv("MGS_TENANT_ID", "common")
    with pytest.raises(AuthError):
        auth._confidential_token("a-secret")


def test_cert_thumbprint_is_sha1_of_der(monkeypatch, tmp_path):
    import base64, hashlib
    from mgs import auth
    der = b"hello-der-bytes"
    pem = ("-----BEGIN CERTIFICATE-----\n"
           + base64.encodebytes(der).decode()
           + "-----END CERTIFICATE-----\n")
    assert auth._cert_thumbprint(pem) == hashlib.sha1(der).hexdigest()


def test_client_credential_prefers_secret_then_cert(monkeypatch, tmp_path):
    from mgs import auth, config
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("MGS_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_CERTIFICATE_PATH", raising=False)
    monkeypatch.delenv("MGS_CLIENT_CERTIFICATE_PATH", raising=False)
    assert auth._client_credential() is None
    # cert only
    import base64
    pem = ("-----BEGIN CERTIFICATE-----\n"
           + base64.encodebytes(b"der").decode()
           + "-----END CERTIFICATE-----\n")
    p = tmp_path / "c.pem"
    p.write_text(pem)
    monkeypatch.setenv("MGS_CLIENT_CERTIFICATE_PATH", str(p))
    cred = auth._client_credential()
    assert isinstance(cred, dict) and "private_key" in cred and "thumbprint" in cred
    # secret wins over cert
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "sec")
    assert auth._client_credential() == "sec"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_auth_app_only.py -v`
Expected: FAIL with `AttributeError: module 'mgs.auth' has no attribute '_confidential_token'`

- [ ] **Step 3: Implement the helpers**

In `src/mgs/auth.py`, add near the top (after `SKEW_SECS`):

```python
GRAPH_RESOURCE = "https://graph.microsoft.com"
GRAPH_DEFAULT_SCOPE = "https://graph.microsoft.com/.default"
_NON_TENANT = {"common", "organizations", "consumers"}
```

Then add these functions (place them after `_effective_scopes`):

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_auth_app_only.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/mgs/auth.py tests/test_auth_app_only.py
git commit -m "feat(auth): app-only primitives — confidential token, cert thumbprint, credential builder"
```

---

## Task 4: Per-mechanism token functions (secret / workload / managed identity)

**Files:**
- Modify: `src/mgs/auth.py`
- Test: `tests/test_auth_app_only.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_auth_app_only.py`:

```python
def test_secret_token_optional_returns_none_when_no_cred(monkeypatch):
    from mgs import auth
    for k in ("AZURE_CLIENT_SECRET", "MGS_CLIENT_SECRET",
              "AZURE_CLIENT_CERTIFICATE_PATH", "MGS_CLIENT_CERTIFICATE_PATH"):
        monkeypatch.delenv(k, raising=False)
    assert auth._secret_token(optional=True) is None


def test_secret_token_required_raises_when_no_cred(monkeypatch):
    from mgs import auth
    for k in ("AZURE_CLIENT_SECRET", "MGS_CLIENT_SECRET",
              "AZURE_CLIENT_CERTIFICATE_PATH", "MGS_CLIENT_CERTIFICATE_PATH"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(AuthError):
        auth._secret_token(optional=False)


def test_workload_token_reads_assertion_file(monkeypatch, tmp_path):
    from mgs import auth
    captured = _fake_msal(monkeypatch)
    monkeypatch.setenv("MGS_TENANT_ID", "contoso")
    monkeypatch.setenv("MGS_CLIENT_ID", "cid")
    tok = tmp_path / "fed"
    tok.write_text("  the-assertion\n")
    monkeypatch.setenv("AZURE_FEDERATED_TOKEN_FILE", str(tok))
    result = auth._workload_token()
    assert result["access_token"] == "app-tok"
    assert captured["confidential"]["cred"] == {"client_assertion": "the-assertion"}


def test_workload_token_required_raises_without_file(monkeypatch):
    from mgs import auth
    monkeypatch.delenv("AZURE_FEDERATED_TOKEN_FILE", raising=False)
    with pytest.raises(AuthError):
        auth._workload_token(optional=False)


def test_mi_token_uses_managed_identity_client(monkeypatch):
    from mgs import auth
    captured = {}

    class FakeMI:
        def __init__(self, identity, http_client=None):
            captured["identity"] = identity
            captured["http"] = http_client

        def acquire_token_for_client(self, resource=None):
            captured["resource"] = resource
            return {"access_token": "mi-tok", "expires_in": 3600}

    fake = types.ModuleType("msal")
    fake.ManagedIdentityClient = FakeMI
    fake.SystemAssignedManagedIdentity = lambda: ("system",)
    fake.UserAssignedManagedIdentity = lambda client_id: ("user", client_id)
    monkeypatch.setitem(sys.modules, "msal", fake)
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(Session=lambda: "sess"))

    # system-assigned when no explicit client id
    for k in ("MGS_CLIENT_ID", "AZURE_CLIENT_ID"):
        monkeypatch.delenv(k, raising=False)
    result = auth._mi_token()
    assert result["access_token"] == "mi-tok"
    assert captured["identity"] == ("system",)
    assert captured["resource"] == "https://graph.microsoft.com"

    # user-assigned when explicit client id set
    monkeypatch.setenv("AZURE_CLIENT_ID", "uami-id")
    auth._mi_token()
    assert captured["identity"] == ("user", "uami-id")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_auth_app_only.py -k "secret_token or workload_token or mi_token" -v`
Expected: FAIL with `AttributeError: module 'mgs.auth' has no attribute '_secret_token'`

- [ ] **Step 3: Implement the mechanisms**

In `src/mgs/auth.py`, add after `_confidential_token`:

```python
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
```

Note: `_mi_token`'s `optional` parameter keeps a uniform signature with the other two (used by the chain in Task 5); managed identity has no cheap "is it present" check, so it always attempts acquisition.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_auth_app_only.py -k "secret_token or workload_token or mi_token" -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/mgs/auth.py tests/test_auth_app_only.py
git commit -m "feat(auth): secret/cert, workload-federation, and managed-identity token functions"
```

---

## Task 5: `_acquire_app_only` — chain + pinned short-circuits

**Files:**
- Modify: `src/mgs/auth.py`
- Test: `tests/test_auth_app_only.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_auth_app_only.py`:

```python
def test_acquire_app_only_pinned_secret_writes_cache(monkeypatch, tmp_path):
    from mgs import auth
    _fake_msal(monkeypatch)
    monkeypatch.setenv("MGS_TENANT_ID", "contoso")
    monkeypatch.setenv("MGS_CLIENT_ID", "cid")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "sec")
    tok = auth._acquire_app_only(str(tmp_path), "secret")
    assert tok == "app-tok"
    # fast-path cache written for reuse
    cached = auth._read_fast(str(tmp_path))
    assert cached["access_token"] == "app-tok"


def test_acquire_app_only_chain_falls_through_to_mi(monkeypatch, tmp_path):
    """app-only mode: no secret, no federated file -> managed identity."""
    from mgs import auth

    class FakeMI:
        def __init__(self, identity, http_client=None):
            pass

        def acquire_token_for_client(self, resource=None):
            return {"access_token": "mi-tok", "expires_in": 3600}

    fake = types.ModuleType("msal")
    fake.ManagedIdentityClient = FakeMI
    fake.SystemAssignedManagedIdentity = lambda: ("system",)
    fake.UserAssignedManagedIdentity = lambda client_id: ("user", client_id)
    monkeypatch.setitem(sys.modules, "msal", fake)
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(Session=lambda: "s"))
    for k in ("AZURE_CLIENT_SECRET", "MGS_CLIENT_SECRET", "AZURE_CLIENT_CERTIFICATE_PATH",
              "MGS_CLIENT_CERTIFICATE_PATH", "AZURE_FEDERATED_TOKEN_FILE",
              "MGS_CLIENT_ID", "AZURE_CLIENT_ID"):
        monkeypatch.delenv(k, raising=False)
    tok = auth._acquire_app_only(str(tmp_path), "app-only")
    assert tok == "mi-tok"


def test_acquire_app_only_pinned_secret_missing_cred_raises(monkeypatch, tmp_path):
    from mgs import auth
    _fake_msal(monkeypatch)
    for k in ("AZURE_CLIENT_SECRET", "MGS_CLIENT_SECRET",
              "AZURE_CLIENT_CERTIFICATE_PATH", "MGS_CLIENT_CERTIFICATE_PATH"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(AuthError):
        auth._acquire_app_only(str(tmp_path), "secret")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_auth_app_only.py -k acquire_app_only -v`
Expected: FAIL with `AttributeError: module 'mgs.auth' has no attribute '_acquire_app_only'`

- [ ] **Step 3: Implement `_acquire_app_only`**

In `src/mgs/auth.py`, add after `_mi_token`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_auth_app_only.py -k acquire_app_only -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/mgs/auth.py tests/test_auth_app_only.py
git commit -m "feat(auth): _acquire_app_only — mechanism chain with pinned short-circuits"
```

---

## Task 6: Route `get_token` and `login` through the auth mode

**Files:**
- Modify: `src/mgs/auth.py`
- Test: `tests/test_auth_app_only.py`, `tests/test_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_auth_app_only.py`:

```python
def test_get_token_routes_app_only(monkeypatch, tmp_path):
    from mgs import auth
    _fake_msal(monkeypatch)
    monkeypatch.delenv("MGS_TOKEN", raising=False)
    monkeypatch.setenv("MGS_AUTH", "secret")
    monkeypatch.setenv("MGS_TENANT_ID", "contoso")
    monkeypatch.setenv("MGS_CLIENT_ID", "cid")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "sec")
    assert auth.get_token(str(tmp_path)) == "app-tok"


def test_get_token_env_and_cache_win_over_app_only(monkeypatch, tmp_path):
    from mgs import auth
    monkeypatch.setenv("MGS_AUTH", "secret")  # would fail (no creds) if reached
    monkeypatch.setenv("MGS_TOKEN", "env-tok")
    assert auth.get_token(str(tmp_path)) == "env-tok"
    monkeypatch.delenv("MGS_TOKEN", raising=False)
    auth._write_fast(str(tmp_path), "cached", 2_000_000_000)
    assert auth.get_token(str(tmp_path)) == "cached"


def test_login_app_only_does_credential_check(monkeypatch, tmp_path):
    from mgs import auth
    _fake_msal(monkeypatch)
    monkeypatch.setenv("MGS_AUTH", "secret")
    monkeypatch.setenv("MGS_TENANT_ID", "contoso")
    monkeypatch.setenv("MGS_CLIENT_ID", "cid")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "sec")
    assert auth.login(str(tmp_path)) == "app-tok"  # no browser
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_auth_app_only.py -k "routes_app_only or env_and_cache or login_app_only" -v`
Expected: FAIL — `get_token` currently ignores `MGS_AUTH` and calls `_acquire_via_msal`, which imports the fake msal but has no `PublicClientApplication` (AttributeError), so `test_get_token_routes_app_only` fails.

- [ ] **Step 3: Route through `resolve_auth_mode`**

In `src/mgs/auth.py`, replace the body of `get_token`:

```python
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
```

And update `login`:

```python
def login(config_dir: str) -> str:
    """Force a fresh login. Delegated: interactive/device. App-only: a non-interactive credential check."""
    mode = config.resolve_auth_mode()
    if mode != "delegated":
        return _acquire_app_only(config_dir, mode)
    return _acquire_via_msal(config_dir, force_interactive=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_auth_app_only.py tests/test_auth.py -v`
Expected: PASS (all app-only tests + existing auth tests unchanged)

- [ ] **Step 5: Commit**

```bash
git add src/mgs/auth.py tests/test_auth_app_only.py
git commit -m "feat(auth): route get_token/login through MGS_AUTH (app-only vs delegated)"
```

---

## Task 7: Surface the auth mode in `mgs auth status`

**Files:**
- Modify: `src/mgs/auth_commands.py`
- Test: `tests/test_auth_commands.py` (create if absent)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_auth_commands.py` (create the file if it does not exist, with the import):

```python
from mgs import auth_commands


def test_status_reports_auth_mode(monkeypatch, tmp_path):
    monkeypatch.delenv("MGS_AUTH", raising=False)
    for k in ("AZURE_CLIENT_SECRET", "MGS_CLIENT_SECRET", "AZURE_FEDERATED_TOKEN_FILE",
              "AZURE_CLIENT_CERTIFICATE_PATH", "MGS_CLIENT_CERTIFICATE_PATH",
              "IDENTITY_ENDPOINT", "MSI_ENDPOINT"):
        monkeypatch.delenv(k, raising=False)
    out = auth_commands.status_value(str(tmp_path))
    assert out["authenticated"] is False
    assert out["mode"] == "delegated"
    monkeypatch.setenv("MGS_AUTH", "managed-identity")
    assert auth_commands.status_value(str(tmp_path))["mode"] == "managed-identity"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_auth_commands.py -v`
Expected: FAIL with `KeyError: 'mode'`

- [ ] **Step 3: Add `mode` to `status_value`**

In `src/mgs/auth_commands.py`, update `status_value` and its import:

```python
from mgs import auth, config


def status_value(config_dir: str) -> dict:
    mode = config.resolve_auth_mode()
    fast = auth._read_fast(config_dir)
    if fast and not auth.is_expired(fast["expires_at"]):
        return {"authenticated": True, "mode": mode, "expires_at": fast["expires_at"]}
    return {"authenticated": False, "mode": mode}
```

(Keep the existing `from mgs.errors import UsageError` import and the rest of the file unchanged.)

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_auth_commands.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/mgs/auth_commands.py tests/test_auth_commands.py
git commit -m "feat(auth): report the active auth mode in mgs auth status"
```

---

## Task 8: Documentation

**Files:**
- Modify: `docs/auth-production.md`
- Modify: `README.md`
- Modify: `src/mgs/skills.py`

No tests; this task ends by regenerating skills and running the full suite.

- [ ] **Step 1: Add an "App-only auth" section to `docs/auth-production.md`**

Insert a new section immediately **after** the "Tenant selection" section and **before** "Token storage":

```markdown
## App-only auth (unattended / server / CI)

Beyond the interactive delegated flows above, `mgs` can authenticate **as itself** with
Microsoft Graph **application** permissions — for daemons, cron jobs, CI, and Azure-hosted
workloads. Set `MGS_AUTH` to choose the track and, optionally, pin one mechanism:

| `MGS_AUTH` | Behavior |
|---|---|
| *(unset)* / `delegated` | Interactive delegated login (browser/device). **Default.** |
| `app-only` | Try, in order: client secret/cert → workload identity federation → managed identity. |
| `secret` | Pin client secret or certificate only. |
| `workload` | Pin workload identity federation (OIDC) only. |
| `managed-identity` (alias `msi`) | Pin the Azure host's managed identity only. |

When `MGS_AUTH` is **unset**, `mgs` auto-selects `app-only` if it detects app-only credentials
in the environment (a client secret, `AZURE_FEDERATED_TOKEN_FILE`, or a managed-identity
endpoint); otherwise it uses the delegated flow. Explicit `MGS_AUTH` always wins.

**App-only uses application permissions, not delegated scopes.** Grant the app the Graph
**application** permissions it needs (e.g. `Mail.Read`, `User.Read.All`) and have an admin
consent to them once in Entra ID. `MGS_SCOPES` applies only to the delegated flow and is
ignored here. App-only also requires a **specific tenant** — set `MGS_TENANT_ID` /
`AZURE_TENANT_ID` (not `common`).

Credentials are read from standard `AZURE_*` variables (with `MGS_*` aliases):

| Purpose | Primary | Alias |
|---|---|---|
| Client id | `AZURE_CLIENT_ID` | `MGS_CLIENT_ID` |
| Tenant id | `AZURE_TENANT_ID` | `MGS_TENANT_ID` |
| Client secret | `AZURE_CLIENT_SECRET` | `MGS_CLIENT_SECRET` |
| Certificate (PEM path) | `AZURE_CLIENT_CERTIFICATE_PATH` | `MGS_CLIENT_CERTIFICATE_PATH` |
| Federated token file (OIDC) | `AZURE_FEDERATED_TOKEN_FILE` | — |
| User-assigned MI client id | `AZURE_CLIENT_ID` | `MGS_CLIENT_ID` |

```bash
# Service principal with a secret
export MGS_AUTH=secret
export AZURE_TENANT_ID=contoso.onmicrosoft.com
export AZURE_CLIENT_ID=<app-id>
export AZURE_CLIENT_SECRET=<secret>
mgs users +me

# Azure VM / Container App with a managed identity
export MGS_AUTH=managed-identity
mgs mail +read

# GitHub Actions via workload identity federation (OIDC)
export MGS_AUTH=workload
# AZURE_CLIENT_ID / AZURE_TENANT_ID / AZURE_FEDERATED_TOKEN_FILE injected by the OIDC step
mgs users +me
```

No `azure-identity` dependency is required — `mgs` implements these flows directly on MSAL.
```

Then, in the existing "Roadmap" section, **remove** the bullet that begins
"**App-only (client-credentials) flow** for unattended/server use…" (it is now implemented).

- [ ] **Step 2: Update the README environment table**

In `README.md`, in the `## Environment variables` table (around line 121-127), add these rows after the `MGS_NO_BROWSER` row:

```markdown
| `MGS_AUTH` | Auth mode: `delegated` (default), `app-only`, `secret`, `workload`, `managed-identity` (see [docs/auth-production.md](docs/auth-production.md)) |
| `AZURE_CLIENT_SECRET` / `MGS_CLIENT_SECRET` | App-only client secret (service principal) |
| `AZURE_CLIENT_CERTIFICATE_PATH` | App-only certificate (PEM) |
| `AZURE_FEDERATED_TOKEN_FILE` | App-only workload identity federation (OIDC) token file |
```

- [ ] **Step 3: Update the skills shared env list**

In `src/mgs/skills.py`, update the `SHARED_MD` "Environment Variables" block (around line 258-261) to:

```python
## Environment Variables

`MGS_TOKEN`, `MGS_CLIENT_ID`/`MGS_TENANT_ID`, `MGS_SCOPES`, `MGS_CONFIG_DIR`, `MGS_NO_BROWSER`,
`AZURE_CLIENT_ID`/`AZURE_TENANT_ID`. For unattended/server use set `MGS_AUTH`
(`app-only`/`secret`/`workload`/`managed-identity`) with `AZURE_CLIENT_SECRET`,
`AZURE_CLIENT_CERTIFICATE_PATH`, or `AZURE_FEDERATED_TOKEN_FILE`.
```

- [ ] **Step 4: Regenerate skills and sync root AGENTS.md**

Run:

```bash
uv run mgs skills generate 2>/dev/null || uv run python -c "from mgs.skills import generate; generate()"
cp skills/AGENTS.md AGENTS.md
```

Expected: the `skills/` tree and `AGENTS.md` regenerate without error. (If the exact generate invocation differs, inspect `src/mgs/cli.py` for the `generate-skills` branch and use that command.)

- [ ] **Step 5: Run the full suite and commit**

Run: `uv run pytest -q`
Expected: PASS (all prior tests + the new app-only/config/commands tests)

```bash
git add docs/auth-production.md README.md src/mgs/skills.py skills AGENTS.md
git commit -m "docs: document app-only auth (MGS_AUTH) across auth guide, README, skills"
```

---

## Task 9: Version bump + final verification

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/mgs/__init__.py`

- [ ] **Step 1: Bump the version**

In `pyproject.toml` change `version = "0.7.2"` to `version = "0.8.0"` (new feature → minor bump).
In `src/mgs/__init__.py` change the fallback `__version__ = "0.7.2"` to `__version__ = "0.8.0"`.

- [ ] **Step 2: Full verification**

Run:

```bash
uv run pytest -q
uv run mgs --help >/dev/null && echo "cli ok"
MGS_AUTH=bogus uv run mgs users +me ; echo "exit=$?"   # expect a usage error, exit 2
```

Expected: all tests pass; `cli ok`; the bogus-mode run prints an `invalid MGS_AUTH` usage error with exit code 2.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml src/mgs/__init__.py
git commit -m "chore: bump version to 0.8.0 (app-only auth)"
```

---

## Self-review notes (for the executor)

- **Spec coverage:** msal-native (Task 3-4, no azure-identity) ✓; secret/cert (Task 3-4) ✓;
  workload federation (Task 4) ✓; managed identity (Task 4) ✓; `MGS_AUTH` select + pin (Task 2,
  5) ✓; ambient auto-detect only when unset (Task 2) ✓; `.default`/application perms + tenant
  guard (Task 3) ✓; `MGS_SCOPES` stays delegated-only (untouched) ✓; fast-path cache above both
  tracks (Task 5-6) ✓; `AZURE_*` primary + `MGS_*` alias (Task 1) ✓; errors via `AuthError`/
  `UsageError` (Task 2-5) ✓; status shows mode (Task 7) ✓; docs (Task 8) ✓.
- **Naming consistency:** `resolve_auth_mode`, `resolve_client_secret`, `resolve_cert_path`,
  `resolve_federated_token_file`, `resolve_explicit_client_id`, `_ambient_app_only`,
  `_confidential_token`, `_client_credential`, `_cert_thumbprint`, `_secret_token`,
  `_workload_token`, `_mi_token`, `_acquire_app_only` — used identically across tasks.
- **Constants:** `GRAPH_RESOURCE`, `GRAPH_DEFAULT_SCOPE`, `_NON_TENANT`, `AUTH_MODES`,
  `_AUTH_ALIASES` defined once (Task 2-3).
```
