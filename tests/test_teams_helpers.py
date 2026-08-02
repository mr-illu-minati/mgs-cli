import argparse

import pytest

from mgs.errors import UsageError
from mgs.executor import opts_from_namespace
from mgs.helpers import registry, teams  # noqa: F401
from mgs.helpers.teams import message_body, teams_send_path


def _run(verb, args):
    helper = registry.get("team", verb)
    p = argparse.ArgumentParser()
    helper.add_arguments(p)
    ns = p.parse_args(args)
    return helper.run("", ns, opts_from_namespace(ns))


def test_send_path_chat_and_channel():
    assert teams_send_path(None, None, "19:abc") == "/chats/19%3Aabc/messages"
    assert teams_send_path("T1", "C1", None) == "/teams/T1/channels/C1/messages"


def test_send_path_requires_target():
    with pytest.raises(UsageError):
        teams_send_path(None, None, None)


def test_message_body():
    assert message_body("hi", False) == {"body": {"contentType": "text", "content": "hi"}}
    assert message_body("<b>x</b>", True)["body"]["contentType"] == "html"


def test_send_dry_run_channel():
    out = _run("+send", ["--team", "T1", "--channel", "C1", "--message", "hi", "--dry-run"])
    assert out["method"] == "POST"
    assert out["url"].endswith("/teams/T1/channels/C1/messages")
    assert out["body"]["body"]["content"] == "hi"


def test_channels_dry_run():
    out = _run("+channels", ["--team", "T1", "--dry-run"])
    assert out["url"].endswith("/teams/T1/channels?%24select=id,displayName")


def test_registered():
    assert registry.get("team", "+send") is not None
    assert registry.get("team", "+channels") is not None
    assert registry.get("team", "+chats") is not None


def test_chats_dry_run_with_mailbox(monkeypatch):
    monkeypatch.setenv("MGS_MAILBOX", "box@contoso.com")
    out = _run("+chats", ["--dry-run"])
    assert "/users/box%40contoso.com/chats" in out["url"]
