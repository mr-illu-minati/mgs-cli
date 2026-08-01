"""Outlook mail +verb helpers, matching the gws Gmail helper set."""

from __future__ import annotations

import argparse

from mgs.executor import Opts
from mgs.helpers import mail_build, registry


def _addr(recipient: dict) -> str:
    e = (recipient or {}).get("emailAddress", {})
    name, address = e.get("name"), e.get("address", "")
    return f"{name} <{address}>" if name else address


def render_message(msg: dict) -> dict:
    """Format a Graph message into clean, readable fields (HTML body -> text)."""
    body = msg.get("body", {}) or {}
    content = body.get("content", "")
    # Graph returns the body type enum lowercase ("html"/"text"); compare case-insensitively.
    is_html = str(body.get("contentType", "")).lower() == "html"
    text = mail_build.html_to_text(content) if is_html else content
    return {
        "id": msg.get("id"),
        "from": _addr(msg.get("from")),
        "to": [_addr(r) for r in msg.get("toRecipients", [])],
        "cc": [_addr(r) for r in msg.get("ccRecipients", [])],
        "subject": msg.get("subject"),
        "received": msg.get("receivedDateTime"),
        "hasAttachments": msg.get("hasAttachments", False),
        "body": text,
    }


def _dry_or_send(method: str, path: str, body: dict | None, opts: Opts, token: str) -> object:
    if opts.dry_run:
        version = "beta" if opts.beta else "v1.0"
        out = {
            "dryRun": True,
            "method": method,
            "url": f"https://graph.microsoft.com/{version}{path}",
        }
        if body is not None:
            out["body"] = body
        return out
    from mgs.client import GraphClient

    client = GraphClient(token, beta=opts.beta)
    return client.request(method, client.full_url(path), body=body)


class SendHelper:
    name = "+send"
    service = "message"
    help = "Send an email (--to/--cc/--bcc --subject --body [--html] [--attach] [--draft])"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--to", help="Recipient(s), comma-separated")
        p.add_argument("--cc", help="CC recipient(s), comma-separated")
        p.add_argument("--bcc", help="BCC recipient(s), comma-separated")
        p.add_argument("--subject", default="", help="Email subject")
        p.add_argument("--body", default="", help="Email body")
        p.add_argument("--html", action="store_true", help="Treat body as HTML")
        p.add_argument("--attach", action="append", help="File to attach (repeatable)")
        p.add_argument("--draft", action="store_true", help="Save as draft instead of sending")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        message = mail_build.build_message(
            ns.subject,
            ns.body,
            html=ns.html,
            to=ns.to,
            cc=ns.cc,
            bcc=ns.bcc,
            attach=ns.attach,
        )
        if ns.draft:
            return _dry_or_send("POST", "/me/messages", message, opts, token)
        return _dry_or_send(
            "POST", "/me/sendMail", {"message": message, "saveToSentItems": True}, opts, token
        )


class ReadHelper:
    name = "+read"
    service = "message"
    help = "Read a message and render clean body/headers"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("id", help="Message id")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        from mgs.validate import encode_path_segment, validate_resource_name

        validate_resource_name(ns.id)
        path = f"/me/messages/{encode_path_segment(ns.id)}"
        if opts.dry_run:
            version = "beta" if opts.beta else "v1.0"
            return {
                "dryRun": True,
                "method": "GET",
                "url": f"https://graph.microsoft.com/{version}{path}",
            }
        from mgs.client import GraphClient

        client = GraphClient(token, beta=opts.beta)
        msg = client.request("GET", client.full_url(path))
        return render_message(msg if isinstance(msg, dict) else {})


def _msg_action_path(message_id: str, action: str) -> str:
    from mgs.validate import encode_path_segment, validate_resource_name

    validate_resource_name(message_id)
    return f"/me/messages/{encode_path_segment(message_id)}/{action}"


class _ReplyBase:
    service = "message"
    action = "reply"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("id", help="Message id")
        p.add_argument("--body", default="", help="Email body")
        p.add_argument("--html", action="store_true", help="Treat body as HTML")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        path = _msg_action_path(ns.id, self.action)
        if ns.html:
            body = {"message": {"body": {"contentType": "HTML", "content": ns.body}}}
        else:
            body = {"comment": ns.body}
        return _dry_or_send("POST", path, body, opts, token)


class ReplyHelper(_ReplyBase):
    name = "+reply"
    action = "reply"
    help = "Reply to a message (threading handled by Graph)"


class ReplyAllHelper(_ReplyBase):
    name = "+reply-all"
    action = "replyAll"
    help = "Reply-all to a message"


class ForwardHelper:
    name = "+forward"
    service = "message"
    help = "Forward a message to new recipients"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("id", help="Message id")
        p.add_argument("--to", required=True, help="Recipient(s), comma-separated")
        p.add_argument("--cc", help="CC recipient(s), comma-separated")
        p.add_argument("--comment", default="", help="Text to include with the forward")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        path = _msg_action_path(ns.id, "forward")
        body: dict = {"comment": ns.comment, "toRecipients": mail_build.parse_recipients(ns.to)}
        cc = mail_build.parse_recipients(ns.cc)
        if cc:
            body["ccRecipients"] = cc
        return _dry_or_send("POST", path, body, opts, token)


def summarize_unread(messages: list[dict]) -> list[dict]:
    """Compact, scan-friendly summary of (already unread, date-desc) messages."""
    return [
        {
            "from": _addr(m.get("from")),
            "subject": m.get("subject"),
            "received": m.get("receivedDateTime"),
            "hasAttachments": m.get("hasAttachments", False),
        }
        for m in messages
    ]


def delta_url(folder: str, *, beta: bool) -> str:
    from mgs.validate import encode_path_segment

    base = "https://graph.microsoft.com/beta" if beta else "https://graph.microsoft.com/v1.0"
    return f"{base}/me/mailFolders/{encode_path_segment(folder)}/messages/delta"


class TriageHelper:
    name = "+triage"
    service = "message"
    help = "Summarize unread mail (ranked, compact) for fast scanning"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--folder", default="inbox", help="Mail folder (wellKnownName or id)")
        p.add_argument("--max", type=int, default=10, help="Max messages to return")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        from mgs.odata import QueryOptions
        from mgs.validate import encode_path_segment

        folder = encode_path_segment(ns.folder)
        query = QueryOptions(
            filter="isRead eq false",
            top=ns.max,
            select="subject,from,receivedDateTime,hasAttachments",
            orderby="receivedDateTime desc",
        ).to_query_string()
        path = f"/me/mailFolders/{folder}/messages{query}"
        if opts.dry_run:
            version = "beta" if opts.beta else "v1.0"
            return {
                "dryRun": True,
                "method": "GET",
                "url": f"https://graph.microsoft.com/{version}{path}",
            }
        from mgs.client import GraphClient

        client = GraphClient(token, beta=opts.beta)
        resp = client.request("GET", client.full_url(path))
        messages = resp.get("value", []) if isinstance(resp, dict) else []
        return {"unread": len(messages), "messages": summarize_unread(messages)}


class WatchHelper:
    name = "+watch"
    service = "message"
    help = "Stream new mail as NDJSON via Graph delta polling"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--folder", default="inbox", help="Mail folder (wellKnownName or id)")
        p.add_argument("--interval", type=int, default=30, help="Poll interval in seconds")
        p.add_argument("--max-iterations", type=int, default=0, help="0 = run until interrupted")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        url = delta_url(ns.folder, beta=opts.beta)
        if opts.dry_run:
            return {"dryRun": True, "method": "GET", "url": url, "interval": ns.interval}
        import json as jsonlib
        import sys
        import time

        from mgs.client import GraphClient
        from mgs.odata import NEXT_LINK

        client = GraphClient(token, beta=opts.beta)
        iterations = 0
        next_url: str | None = url
        while True:
            page = client.request("GET", next_url)
            if isinstance(page, dict):
                for item in page.get("value", []):
                    sys.stdout.write(jsonlib.dumps(item) + "\n")
                    sys.stdout.flush()
                next_url = page.get(NEXT_LINK) or page.get("@odata.deltaLink") or next_url
            iterations += 1
            if ns.max_iterations and iterations >= ns.max_iterations:
                return {"watched": ns.folder, "iterations": iterations}
            time.sleep(max(ns.interval, 1))


registry.register(SendHelper())
registry.register(ReadHelper())
registry.register(ReplyHelper())
registry.register(ReplyAllHelper())
registry.register(ForwardHelper())
registry.register(TriageHelper())
registry.register(WatchHelper())
