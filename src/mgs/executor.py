"""Translate parsed args into an OData request plan, then dry-run or execute it."""

from __future__ import annotations

import argparse
import json as jsonlib
from dataclasses import dataclass
from urllib.parse import quote_plus

from mgs.errors import UsageError
from mgs.odata import QueryOptions
from mgs.services import ServiceEntry
from mgs.validate import encode_path_segment, validate_resource_name

GENERIC_VERBS = {"list", "get", "create", "update", "delete"}


@dataclass
class Opts:
    select: str | None = None
    filter: str | None = None
    orderby: str | None = None
    expand: str | None = None
    search: str | None = None
    top: int | None = None
    skip: int | None = None
    page_all: bool = False
    dry_run: bool = False
    beta: bool = False
    json: str | None = None
    params: str | None = None
    folder: str | None = None


@dataclass
class RequestPlan:
    method: str
    path: str
    query: str
    body: dict | None = None


def opts_from_namespace(ns: argparse.Namespace) -> Opts:
    g = lambda n, d=None: getattr(ns, n, d)
    return Opts(
        select=g("select"),
        filter=g("filter"),
        orderby=g("orderby"),
        expand=g("expand"),
        search=g("search"),
        top=g("top"),
        skip=g("skip"),
        page_all=g("page_all", False),
        dry_run=g("dry_run", False),
        beta=g("beta", False),
        json=g("json"),
        params=g("params"),
        folder=g("folder"),
    )


def _parse_json(value: str | None, what: str) -> dict | None:
    if value is None:
        return None
    try:
        return jsonlib.loads(value)
    except ValueError as e:
        raise UsageError(f"--{what} is not valid JSON: {e}")


def _query(opts: Opts) -> str:
    base = QueryOptions(
        select=opts.select,
        filter=opts.filter,
        orderby=opts.orderby,
        expand=opts.expand,
        search=opts.search,
        top=opts.top,
        skip=opts.skip,
    ).to_query_string()
    extra = _parse_json(opts.params, "params") or {}
    if not extra:
        return base
    pairs = "&".join(f"{quote_plus(str(k))}={quote_plus(str(v))}" for k, v in extra.items())
    return f"{base}&{pairs}" if base else f"?{pairs}"


def _list_path(svc: ServiceEntry, opts: Opts) -> str:
    if opts.folder and svc.entity_type == "message":
        return f"/me/mailFolders/{encode_path_segment(opts.folder)}/messages"
    return svc.root_path


def _id_path(svc: ServiceEntry, id: str | None) -> str:
    if id is None:
        raise UsageError("this command requires an id")
    if svc.entity_type == "driveItem":
        from mgs.drivepath import drive_item_base

        return drive_item_base(id)
    validate_resource_name(id)
    return f"{svc.root_path}/{encode_path_segment(id)}"


def build_plan(svc: ServiceEntry, verb: str, id: str | None, opts: Opts) -> RequestPlan:
    query = _query(opts)
    if verb == "list":
        return RequestPlan("GET", _list_path(svc, opts), query)
    if verb == "get":
        return RequestPlan("GET", _id_path(svc, id), query)
    if verb == "create":
        return RequestPlan("POST", svc.root_path, query, body=_parse_json(opts.json, "json"))
    if verb == "update":
        return RequestPlan("PATCH", _id_path(svc, id), query, body=_parse_json(opts.json, "json"))
    if verb == "delete":
        return RequestPlan("DELETE", _id_path(svc, id), query)
    # Bound action: POST {root}/{id}/{action}
    action = validate_resource_name(verb)
    path = f"{_id_path(svc, id)}/{encode_path_segment(action)}"
    return RequestPlan("POST", path, query, body=_parse_json(opts.json, "json"))


def execute(plan: RequestPlan, opts: Opts, token: str) -> object:
    if opts.dry_run:
        version = "beta" if opts.beta else "v1.0"
        out: dict = {
            "dryRun": True,
            "method": plan.method,
            "url": f"https://graph.microsoft.com/{version}{plan.path}{plan.query}",
        }
        if plan.body is not None:
            out["body"] = plan.body
        return out
    from mgs.client import GraphClient  # lazy: pulls urllib only on real requests

    client = GraphClient(token, beta=opts.beta)
    url = client.full_url(plan.path, plan.query)
    if opts.page_all and plan.method == "GET":
        return client.request_all(url)
    return client.request(plan.method, url, body=plan.body)
