from mgs.auth import _read_fast, _write_fast, get_token, is_expired


def test_is_expired_with_skew():
    assert not is_expired(2_000_000_000)  # far future
    assert is_expired(0)  # past


def test_fast_token_round_trip(tmp_path):
    _write_fast(str(tmp_path), "abc", 2_000_000_000)
    got = _read_fast(str(tmp_path))
    assert got["access_token"] == "abc"
    assert got["expires_at"] == 2_000_000_000


def test_get_token_prefers_env(monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_TOKEN", "env-token")
    assert get_token(str(tmp_path)) == "env-token"


def test_get_token_uses_valid_fast_cache_without_msal(monkeypatch, tmp_path):
    monkeypatch.delenv("MGS_TOKEN", raising=False)
    _write_fast(str(tmp_path), "cached", 2_000_000_000)
    # If this tried to import/use msal it would attempt network; a valid cache must not.
    assert get_token(str(tmp_path)) == "cached"


def test_scopes_include_teams_and_notes():
    from mgs.auth import SCOPES

    for s in (
        "Team.ReadBasic.All",
        "Channel.ReadBasic.All",
        "ChannelMessage.Send",
        "Chat.ReadWrite",
        "Notes.ReadWrite",
    ):
        assert s in SCOPES


def test_effective_scopes_default_and_override(monkeypatch):
    from mgs import auth

    monkeypatch.delenv("MGS_SCOPES", raising=False)
    assert auth._effective_scopes() == auth.SCOPES
    monkeypatch.setenv("MGS_SCOPES", "Mail.ReadWrite Mail.Send")
    assert auth._effective_scopes() == ["Mail.ReadWrite", "Mail.Send"]
