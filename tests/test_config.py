from pathlib import Path

import pytest

from mgs.config import BUILTIN_CLIENT_ID, config_dir, resolve_client_id, resolve_tenant
from mgs.errors import UsageError


def test_tenant_defaults_to_common(monkeypatch):
    monkeypatch.delenv("MGS_TENANT_ID", raising=False)
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    assert resolve_tenant() == "common"


def test_mgs_client_id_overrides_builtin(monkeypatch):
    monkeypatch.setenv("MGS_CLIENT_ID", "custom-123")
    assert resolve_client_id() == "custom-123"
    monkeypatch.delenv("MGS_CLIENT_ID")
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    assert resolve_client_id() == BUILTIN_CLIENT_ID


def test_config_dir_override(monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path / "x"))
    assert config_dir() == Path(tmp_path / "x")


def test_resolve_scopes(monkeypatch):
    from mgs.config import resolve_scopes

    monkeypatch.delenv("MGS_SCOPES", raising=False)
    assert resolve_scopes() is None
    monkeypatch.setenv("MGS_SCOPES", "Mail.Read Mail.Send")
    assert resolve_scopes() == ["Mail.Read", "Mail.Send"]
    monkeypatch.setenv("MGS_SCOPES", "Mail.Read, Mail.Send")
    assert resolve_scopes() == ["Mail.Read", "Mail.Send"]


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


def _clear_auth_env(monkeypatch):
    for k in (
        "MGS_AUTH",
        "AZURE_CLIENT_SECRET",
        "MGS_CLIENT_SECRET",
        "AZURE_CLIENT_CERTIFICATE_PATH",
        "MGS_CLIENT_CERTIFICATE_PATH",
        "AZURE_FEDERATED_TOKEN_FILE",
        "IDENTITY_ENDPOINT",
        "MSI_ENDPOINT",
    ):
        monkeypatch.delenv(k, raising=False)


def test_auth_mode_defaults_to_delegated(monkeypatch):
    from mgs import config

    _clear_auth_env(monkeypatch)
    assert config.resolve_auth_mode() == "delegated"


def test_auth_mode_explicit_values_and_aliases(monkeypatch):
    from mgs import config

    _clear_auth_env(monkeypatch)
    for raw, expected in [
        ("app-only", "app-only"),
        ("secret", "secret"),
        ("workload", "workload"),
        ("managed-identity", "managed-identity"),
        ("msi", "managed-identity"),
        ("MSI", "managed-identity"),
        ("interactive", "delegated"),
        ("delegated", "delegated"),
    ]:
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
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "sec")
    assert config.resolve_auth_mode() == "app-only"
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("IDENTITY_ENDPOINT", "http://169.254.169.254/")
    assert config.resolve_auth_mode() == "app-only"
    monkeypatch.setenv("MGS_AUTH", "delegated")
    assert config.resolve_auth_mode() == "delegated"
