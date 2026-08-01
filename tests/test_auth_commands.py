from mgs.auth_commands import run, status_value


def test_status_when_logged_out(tmp_path):
    assert status_value(str(tmp_path)) == {"authenticated": False}


def test_run_status_returns_value(tmp_path):
    assert run("status", str(tmp_path)) == {"authenticated": False}


def test_run_logout_is_idempotent(tmp_path):
    assert run("logout", str(tmp_path)) == {"authenticated": False, "loggedOut": True}
