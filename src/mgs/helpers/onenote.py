"""OneNote +verb helper (create a page)."""

from __future__ import annotations

import argparse

from mgs.executor import Opts
from mgs.helpers import onenote_build, registry
from mgs.userpath import resolve_user_path


def _base(beta: bool) -> str:
    return "https://graph.microsoft.com/beta" if beta else "https://graph.microsoft.com/v1.0"


class WriteHelper:
    name = "+write"
    service = "onenotePage"
    help = "Create a OneNote page (--title, --content, [--html], [--section])"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--title", required=True, help="Page title")
        p.add_argument("--content", default="", help="Page content (HTML or plain text)")
        p.add_argument("--html", action="store_true", help="Treat --content as HTML fragment")
        p.add_argument("--section", help="Target section id (default: default notebook)")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        path = resolve_user_path(onenote_build.pages_path(ns.section))
        page = onenote_build.build_page_html(ns.title, ns.content, ns.html)
        url = _base(opts.beta) + path
        if opts.dry_run:
            return {
                "dryRun": True,
                "method": "POST",
                "url": url,
                "contentType": "text/html",
                "html": page,
            }
        from mgs.helpers import httpio

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "text/html"}
        return httpio.post_bytes(url, page.encode("utf-8"), headers)


registry.register(WriteHelper())
