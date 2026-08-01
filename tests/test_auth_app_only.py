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
                "client_id": client_id,
                "authority": authority,
                "cred": client_credential,
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
    import base64
    import hashlib

    from mgs import auth

    der = b"hello-der-bytes"
    pem = (
        "-----BEGIN CERTIFICATE-----\n"
        + base64.encodebytes(der).decode()
        + "-----END CERTIFICATE-----\n"
    )
    assert auth._cert_thumbprint(pem) == hashlib.sha1(der).hexdigest()


def test_client_credential_prefers_secret_then_cert(monkeypatch, tmp_path):
    import base64

    from mgs import auth

    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("MGS_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_CERTIFICATE_PATH", raising=False)
    monkeypatch.delenv("MGS_CLIENT_CERTIFICATE_PATH", raising=False)
    assert auth._client_credential() is None
    pem = (
        "-----BEGIN CERTIFICATE-----\n"
        + base64.encodebytes(b"der").decode()
        + "-----END CERTIFICATE-----\n"
    )
    p = tmp_path / "c.pem"
    p.write_text(pem)
    monkeypatch.setenv("MGS_CLIENT_CERTIFICATE_PATH", str(p))
    cred = auth._client_credential()
    assert isinstance(cred, dict) and "private_key" in cred and "thumbprint" in cred
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "sec")
    assert auth._client_credential() == "sec"


def test_secret_token_optional_returns_none_when_no_cred(monkeypatch):
    from mgs import auth

    for k in (
        "AZURE_CLIENT_SECRET",
        "MGS_CLIENT_SECRET",
        "AZURE_CLIENT_CERTIFICATE_PATH",
        "MGS_CLIENT_CERTIFICATE_PATH",
    ):
        monkeypatch.delenv(k, raising=False)
    assert auth._secret_token(optional=True) is None


def test_secret_token_required_raises_when_no_cred(monkeypatch):
    from mgs import auth

    for k in (
        "AZURE_CLIENT_SECRET",
        "MGS_CLIENT_SECRET",
        "AZURE_CLIENT_CERTIFICATE_PATH",
        "MGS_CLIENT_CERTIFICATE_PATH",
    ):
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

    for k in ("MGS_CLIENT_ID", "AZURE_CLIENT_ID"):
        monkeypatch.delenv(k, raising=False)
    result = auth._mi_token()
    assert result["access_token"] == "mi-tok"
    assert captured["identity"] == ("system",)
    assert captured["resource"] == "https://graph.microsoft.com"

    monkeypatch.setenv("AZURE_CLIENT_ID", "uami-id")
    auth._mi_token()
    assert captured["identity"] == ("user", "uami-id")


def test_acquire_app_only_pinned_secret_writes_cache(monkeypatch, tmp_path):
    from mgs import auth

    _fake_msal(monkeypatch)
    monkeypatch.setenv("MGS_TENANT_ID", "contoso")
    monkeypatch.setenv("MGS_CLIENT_ID", "cid")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "sec")
    tok = auth._acquire_app_only(str(tmp_path), "secret")
    assert tok == "app-tok"
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
    for k in (
        "AZURE_CLIENT_SECRET",
        "MGS_CLIENT_SECRET",
        "AZURE_CLIENT_CERTIFICATE_PATH",
        "MGS_CLIENT_CERTIFICATE_PATH",
        "AZURE_FEDERATED_TOKEN_FILE",
        "MGS_CLIENT_ID",
        "AZURE_CLIENT_ID",
    ):
        monkeypatch.delenv(k, raising=False)
    tok = auth._acquire_app_only(str(tmp_path), "app-only")
    assert tok == "mi-tok"


def test_acquire_app_only_pinned_secret_missing_cred_raises(monkeypatch, tmp_path):
    from mgs import auth

    _fake_msal(monkeypatch)
    for k in (
        "AZURE_CLIENT_SECRET",
        "MGS_CLIENT_SECRET",
        "AZURE_CLIENT_CERTIFICATE_PATH",
        "MGS_CLIENT_CERTIFICATE_PATH",
    ):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(AuthError):
        auth._acquire_app_only(str(tmp_path), "secret")


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
