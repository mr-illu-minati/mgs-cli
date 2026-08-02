import pytest

from mgs.errors import UsageError

CLEAR = (
    "MGS_MAILBOX",
    "MGS_DEFAULT_MAILBOX",
    "MGS_AUTH",
    "AZURE_CLIENT_SECRET",
    "MGS_CLIENT_SECRET",
    "AZURE_CLIENT_CERTIFICATE_PATH",
    "MGS_CLIENT_CERTIFICATE_PATH",
    "AZURE_FEDERATED_TOKEN_FILE",
    "IDENTITY_ENDPOINT",
    "MSI_ENDPOINT",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    from mgs import config

    for key in CLEAR:
        monkeypatch.delenv(key, raising=False)
    config.set_mailbox(None)
    yield
    config.set_mailbox(None)


def test_no_mailbox_delegated_leaves_me_path_unchanged():
    from mgs.userpath import resolve_user_path

    assert resolve_user_path("/me/messages") == "/me/messages"


def test_explicit_mailbox_swaps_me_prefix():
    from mgs.userpath import resolve_user_path

    assert (
        resolve_user_path("/me/messages", "sandbox-cabinet@contoso.com")
        == "/users/sandbox-cabinet%40contoso.com/messages"
    )


def test_non_me_path_unchanged_even_with_mailbox():
    from mgs.userpath import resolve_user_path

    assert resolve_user_path("/users/x/messages", "a@b.c") == "/users/x/messages"
    assert resolve_user_path("/teams/1/channels", "a@b.c") == "/teams/1/channels"


def test_bare_me_swaps_without_trailing_slash():
    from mgs.userpath import resolve_user_path

    assert resolve_user_path("/me", "a@b.c") == "/users/a%40b.c"


def test_me_prefix_must_be_a_segment():
    from mgs.userpath import resolve_user_path

    # /messages or /메... — a path like /messages starting with "/me" chars but not
    # the /me segment must never be rewritten.
    assert resolve_user_path("/messages", "a@b.c") == "/messages"


def test_mgs_mailbox_env_swaps_in_delegated_mode(monkeypatch):
    from mgs.userpath import resolve_user_path

    monkeypatch.setenv("MGS_MAILBOX", "shared@contoso.com")
    assert resolve_user_path("/me/events") == "/users/shared%40contoso.com/events"


def test_default_mailbox_applies_only_in_app_only_mode(monkeypatch):
    from mgs.userpath import resolve_user_path

    monkeypatch.setenv("MGS_DEFAULT_MAILBOX", "sandbox@contoso.com")
    # Delegated: default mailbox is ignored, /me/ stays.
    assert resolve_user_path("/me/messages") == "/me/messages"
    # App-only: default mailbox kicks in.
    monkeypatch.setenv("MGS_AUTH", "app-only")
    assert resolve_user_path("/me/messages") == "/users/sandbox%40contoso.com/messages"


def test_app_only_me_path_without_mailbox_raises(monkeypatch):
    from mgs.userpath import resolve_user_path

    monkeypatch.setenv("MGS_AUTH", "app-only")
    with pytest.raises(UsageError, match="--mailbox|MGS_DEFAULT_MAILBOX"):
        resolve_user_path("/me/messages")


def test_app_only_non_me_path_needs_no_mailbox(monkeypatch):
    from mgs.userpath import resolve_user_path

    monkeypatch.setenv("MGS_AUTH", "app-only")
    assert resolve_user_path("/users/x@y.z/messages") == "/users/x@y.z/messages"


def test_cli_override_wins_over_env(monkeypatch):
    from mgs import config
    from mgs.userpath import resolve_user_path

    monkeypatch.setenv("MGS_MAILBOX", "env@contoso.com")
    config.set_mailbox("flag@contoso.com")
    assert resolve_user_path("/me/messages") == "/users/flag%40contoso.com/messages"


def test_resolve_mailbox_precedence(monkeypatch):
    from mgs import config

    assert config.resolve_mailbox() is None
    monkeypatch.setenv("MGS_AUTH", "app-only")
    monkeypatch.setenv("MGS_DEFAULT_MAILBOX", "default@c.com")
    assert config.resolve_mailbox() == "default@c.com"
    monkeypatch.setenv("MGS_MAILBOX", "env@c.com")
    assert config.resolve_mailbox() == "env@c.com"
    config.set_mailbox("flag@c.com")
    assert config.resolve_mailbox() == "flag@c.com"
