import argparse

from mgs.executor import opts_from_namespace
from mgs.helpers import (
    mail,  # noqa: F401  (registers helpers)
    registry,
)
from mgs.helpers.mail import delta_url, render_message, summarize_unread


def _run(verb, args):
    helper = registry.get("message", verb)
    p = argparse.ArgumentParser()
    helper.add_arguments(p)
    ns = p.parse_args(args)
    opts = opts_from_namespace(ns)
    return helper.run("", ns, opts)  # token unused on dry-run


def test_send_dry_run_builds_sendmail():
    out = _run("+send", ["--to", "a@x.com", "--subject", "Hi", "--body", "Yo", "--dry-run"])
    assert out["method"] == "POST"
    assert out["url"].endswith("/me/sendMail")
    assert out["body"]["message"]["toRecipients"][0]["emailAddress"]["address"] == "a@x.com"
    assert out["body"]["saveToSentItems"] is True


def test_send_draft_dry_run_posts_messages():
    out = _run(
        "+send", ["--to", "a@x.com", "--subject", "Hi", "--body", "Yo", "--draft", "--dry-run"]
    )
    assert out["url"].endswith("/me/messages")
    assert out["body"]["subject"] == "Hi"


def test_read_renders_clean_message():
    msg = {
        "subject": "Q3",
        "from": {"emailAddress": {"name": "Al", "address": "al@x.com"}},
        "toRecipients": [{"emailAddress": {"address": "me@x.com"}}],
        "receivedDateTime": "2026-06-01T10:00:00Z",
        # Graph v1.0 returns the body type enum lowercase ("html"), not "HTML".
        "body": {"contentType": "html", "content": "<p>Hello <b>team</b></p>"},
        "hasAttachments": False,
    }
    out = render_message(msg)
    assert out["from"] == "Al <al@x.com>"
    assert out["subject"] == "Q3"
    assert out["body"] == "Hello team"


def test_read_html_contenttype_is_case_insensitive():
    for ct in ("html", "HTML", "Html"):
        msg = {"body": {"contentType": ct, "content": "<b>x</b>"}}
        assert render_message(msg)["body"] == "x"


def test_registered_helpers_present():
    assert registry.get("message", "+send") is not None
    assert registry.get("message", "+read") is not None


def test_reply_dry_run():
    out = _run("+reply", ["AAA", "--body", "Thanks", "--dry-run"])
    assert out["method"] == "POST"
    assert out["url"].endswith("/me/messages/AAA/reply")
    assert out["body"]["comment"] == "Thanks"


def test_reply_all_dry_run():
    out = _run("+reply-all", ["AAA", "--body", "Thanks", "--dry-run"])
    assert out["url"].endswith("/me/messages/AAA/replyAll")


def test_forward_dry_run():
    out = _run("+forward", ["AAA", "--to", "b@x.com", "--comment", "fyi", "--dry-run"])
    assert out["url"].endswith("/me/messages/AAA/forward")
    assert out["body"]["toRecipients"][0]["emailAddress"]["address"] == "b@x.com"
    assert out["body"]["comment"] == "fyi"


def test_summarize_unread():
    msgs = [
        {
            "from": {"emailAddress": {"name": "Al", "address": "al@x.com"}},
            "subject": "Budget",
            "receivedDateTime": "2026-06-01T10:00:00Z",
            "hasAttachments": True,
        },
        {
            "from": {"emailAddress": {"address": "b@x.com"}},
            "subject": "Lunch?",
            "receivedDateTime": "2026-06-01T09:00:00Z",
            "hasAttachments": False,
        },
    ]
    out = summarize_unread(msgs)
    assert out[0] == {
        "from": "Al <al@x.com>",
        "subject": "Budget",
        "received": "2026-06-01T10:00:00Z",
        "hasAttachments": True,
    }
    assert out[1]["from"] == "b@x.com"


def test_triage_dry_run_targets_unread_folder():
    out = _run("+triage", ["--folder", "inbox", "--max", "5", "--dry-run"])
    assert (
        out["url"].endswith(
            "/me/mailFolders/inbox/messages?%24filter=isRead+eq+false&%24top=5"
            "&%24select=subject%2Cfrom%2CreceivedDateTime%2ChasAttachments"
            "&%24orderby=receivedDateTime+desc"
        )
        or "isRead" in out["url"]
    )


def test_delta_url():
    assert delta_url("inbox", beta=False) == (
        "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages/delta"
    )
    assert delta_url("inbox", beta=True).startswith("https://graph.microsoft.com/beta/")


def test_send_dry_run_with_mailbox(monkeypatch):
    monkeypatch.setenv("MGS_MAILBOX", "box@contoso.com")
    out = _run("+send", ["--to", "a@x.com", "--subject", "Hi", "--body", "Yo", "--dry-run"])
    assert out["url"].endswith("/users/box%40contoso.com/sendMail")


def test_triage_dry_run_with_mailbox(monkeypatch):
    monkeypatch.setenv("MGS_MAILBOX", "box@contoso.com")
    out = _run("+triage", ["--folder", "inbox", "--dry-run"])
    assert "/users/box%40contoso.com/mailFolders/inbox/messages" in out["url"]


def test_delta_url_with_mailbox(monkeypatch):
    monkeypatch.setenv("MGS_MAILBOX", "box@contoso.com")
    assert delta_url("inbox", beta=False) == (
        "https://graph.microsoft.com/v1.0/users/box%40contoso.com/mailFolders/inbox/messages/delta"
    )


def test_send_dry_run_with_from_and_header():
    out = _run(
        "+send",
        [
            "--to",
            "a@x.com",
            "--subject",
            "Hi",
            "--body",
            "Yo",
            "--from",
            "sandbox-employeur@contoso.com",
            "--header",
            "X-Sandbox-Persona: employeur",
            "--dry-run",
        ],
    )
    msg = out["body"]["message"]
    assert msg["from"]["emailAddress"]["address"] == "sandbox-employeur@contoso.com"
    assert msg["internetMessageHeaders"] == [{"name": "X-Sandbox-Persona", "value": "employeur"}]


def test_send_draft_dry_run_with_from():
    out = _run(
        "+send",
        [
            "--to",
            "a@x.com",
            "--subject",
            "Hi",
            "--body",
            "Yo",
            "--from",
            "alias@contoso.com",
            "--draft",
            "--dry-run",
        ],
    )
    assert out["body"]["from"]["emailAddress"]["address"] == "alias@contoso.com"
