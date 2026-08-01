"""Microsoft Teams +verb helpers (send, channels, chats)."""

from __future__ import annotations

import argparse

from mgs.errors import UsageError
from mgs.executor import Opts
from mgs.helpers import registry
from mgs.validate import encode_path_segment, validate_resource_name


def _base(beta: bool) -> str:
    return "https://graph.microsoft.com/beta" if beta else "https://graph.microsoft.com/v1.0"


def teams_send_path(team: str | None, channel: str | None, chat: str | None) -> str:
    if chat:
        validate_resource_name(chat)
        return f"/chats/{encode_path_segment(chat)}/messages"
    if team and channel:
        validate_resource_name(team)
        validate_resource_name(channel)
        return (
            f"/teams/{encode_path_segment(team)}/channels/{encode_path_segment(channel)}/messages"
        )
    raise UsageError("provide --chat, or both --team and --channel")


def message_body(text: str, html: bool) -> dict:
    return {"body": {"contentType": "html" if html else "text", "content": text}}


class SendHelper:
    name = "+send"
    service = "team"
    help = "Send a Teams message to a channel (--team/--channel) or chat (--chat)"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--team", help="Team id")
        p.add_argument("--channel", help="Channel id")
        p.add_argument("--chat", help="Chat id")
        p.add_argument("--message", required=True, help="Message text")
        p.add_argument("--html", action="store_true", help="Treat message as HTML")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        path = teams_send_path(ns.team, ns.channel, ns.chat)
        body = message_body(ns.message, ns.html)
        if opts.dry_run:
            return {"dryRun": True, "method": "POST", "url": _base(opts.beta) + path, "body": body}
        from mgs.client import GraphClient

        c = GraphClient(token, beta=opts.beta)
        return c.request("POST", c.full_url(path), body=body)


class ChannelsHelper:
    name = "+channels"
    service = "team"
    help = "List channels in a team"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--team", required=True, help="Team id")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        validate_resource_name(ns.team)
        path = f"/teams/{encode_path_segment(ns.team)}/channels?%24select=id,displayName"
        if opts.dry_run:
            return {"dryRun": True, "method": "GET", "url": _base(opts.beta) + path}
        from mgs.client import GraphClient

        c = GraphClient(token, beta=opts.beta)
        resp = c.request("GET", c.full_url(path))
        items = resp.get("value", []) if isinstance(resp, dict) else []
        return [{"id": x.get("id"), "name": x.get("displayName")} for x in items]


class ChatsHelper:
    name = "+chats"
    service = "team"
    help = "List your recent chats (for discovering chat ids)"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--max", type=int, default=20, help="Max chats to return")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        path = f"/me/chats?%24top={ns.max}"
        if opts.dry_run:
            return {"dryRun": True, "method": "GET", "url": _base(opts.beta) + path}
        from mgs.client import GraphClient

        c = GraphClient(token, beta=opts.beta)
        resp = c.request("GET", c.full_url(path))
        items = resp.get("value", []) if isinstance(resp, dict) else []
        return [
            {"id": x.get("id"), "topic": x.get("topic"), "chatType": x.get("chatType")}
            for x in items
        ]


registry.register(SendHelper())
registry.register(ChannelsHelper())
registry.register(ChatsHelper())
