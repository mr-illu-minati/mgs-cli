from mgs.auth_commands import run, status_value


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


def test_status_when_logged_out(monkeypatch, tmp_path):
    _clear_auth_env(monkeypatch)
    assert status_value(str(tmp_path)) == {"authenticated": False, "mode": "delegated"}


def test_run_status_returns_value(monkeypatch, tmp_path):
    _clear_auth_env(monkeypatch)
    assert run("status", str(tmp_path)) == {"authenticated": False, "mode": "delegated"}


def test_run_logout_is_idempotent(tmp_path):
    assert run("logout", str(tmp_path)) == {"authenticated": False, "loggedOut": True}


def test_status_reports_auth_mode(monkeypatch, tmp_path):
    _clear_auth_env(monkeypatch)
    out = status_value(str(tmp_path))
    assert out["authenticated"] is False
    assert out["mode"] == "delegated"
    monkeypatch.setenv("MGS_AUTH", "managed-identity")
    assert status_value(str(tmp_path))["mode"] == "managed-identity"
