from pathlib import Path

from mgs.config import BUILTIN_CLIENT_ID, config_dir, resolve_client_id, resolve_tenant


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
