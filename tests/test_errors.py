from mgs.errors import AuthError, HttpError, MgsError, UsageError


def test_auth_error_exit_code_and_json():
    e = AuthError("no token")
    assert e.exit_code == 3
    assert e.to_json() == {"error": {"kind": "auth", "message": "no token"}}


def test_http_error_carries_status():
    e = HttpError("Not Found", status=404)
    assert e.exit_code == 4
    assert e.to_json()["error"]["status"] == 404


def test_base_defaults():
    assert isinstance(UsageError("x"), MgsError)
    assert UsageError("x").exit_code == 2
