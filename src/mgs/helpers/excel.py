"""Excel +verb helpers (read a range, append a row to a table)."""

from __future__ import annotations

import argparse

from mgs.executor import Opts
from mgs.helpers import excel_build, registry
from mgs.userpath import resolve_user_path


def _base(beta: bool) -> str:
    return "https://graph.microsoft.com/beta" if beta else "https://graph.microsoft.com/v1.0"


class ReadHelper:
    name = "+read"
    service = "workbook"
    help = "Read an Excel worksheet range or usedRange"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--file", required=True, help="Workbook drive item id or /path")
        p.add_argument("--sheet", default="Sheet1", help="Worksheet name")
        p.add_argument("--range", help="A1 address, e.g. A1:C10 (default: usedRange)")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        path = resolve_user_path(excel_build.read_range_path(ns.file, ns.sheet, ns.range))
        if opts.dry_run:
            return {"dryRun": True, "method": "GET", "url": _base(opts.beta) + path}
        from mgs.client import GraphClient

        c = GraphClient(token, beta=opts.beta)
        resp = c.request("GET", c.full_url(path))
        if not isinstance(resp, dict):
            return {"address": None, "values": []}
        return {"address": resp.get("address"), "values": resp.get("values", [])}


class AppendHelper:
    name = "+append"
    service = "workbook"
    help = "Append a row to an Excel table"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--file", required=True, help="Workbook drive item id or /path")
        p.add_argument("--table", default="Table1", help="Table name")
        p.add_argument("--values", required=True, help="Comma-separated cell values")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        path = resolve_user_path(excel_build.append_path(ns.file, ns.table))
        body = {"values": excel_build.coerce_values(ns.values)}
        if opts.dry_run:
            return {"dryRun": True, "method": "POST", "url": _base(opts.beta) + path, "body": body}
        from mgs.client import GraphClient

        c = GraphClient(token, beta=opts.beta)
        return c.request("POST", c.full_url(path), body=body)


registry.register(ReadHelper())
registry.register(AppendHelper())
