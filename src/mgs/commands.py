"""Build a per-service argparse parser: list/get/create/update/delete + registered helpers."""

from __future__ import annotations

import argparse

from mgs.services import ServiceEntry


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--dry-run", action="store_true", help="Print the request without executing it")
    p.add_argument("--beta", action="store_true", help="Target the Graph beta endpoint")
    p.add_argument("--params", help="Extra OData query params as a JSON object")


def _query(p: argparse.ArgumentParser) -> None:
    p.add_argument("--select", help="OData $select (comma-separated fields)")
    p.add_argument("--filter", help="OData $filter expression")
    p.add_argument("--orderby", help="OData $orderby expression")
    p.add_argument("--expand", help="OData $expand expression")
    p.add_argument("--search", help="OData $search expression")
    p.add_argument("--top", type=int, help="OData $top (page size)")
    p.add_argument("--skip", type=int, help="OData $skip")
    p.add_argument("--page-all", action="store_true", help="Follow @odata.nextLink and return all pages")


def build_service_parser(svc: ServiceEntry) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"mgs {svc.aliases[0]}", description=svc.description)
    sub = parser.add_subparsers(dest="verb", required=True)

    lst = sub.add_parser("list", help=f"List {svc.entity_type} items")
    _query(lst)
    lst.add_argument("--folder", help="Scope to a mail folder (wellKnownName or id; mail only)")
    _common(lst)

    get = sub.add_parser("get", help=f"Get a single {svc.entity_type} by id")
    get.add_argument("id", help="Resource id")
    _query(get)
    _common(get)

    create = sub.add_parser("create", help=f"Create a {svc.entity_type} (POST)")
    create.add_argument("--json", help="Request body as JSON")
    _common(create)

    update = sub.add_parser("update", help=f"Update a {svc.entity_type} by id (PATCH)")
    update.add_argument("id", help="Resource id")
    update.add_argument("--json", help="Request body as JSON")
    _common(update)

    delete = sub.add_parser("delete", help=f"Delete a {svc.entity_type} by id (DELETE)")
    delete.add_argument("id", help="Resource id")
    _common(delete)

    # Registered +verb helpers for this service.
    from mgs.helpers import registry

    for helper in registry.for_service(svc.entity_type):
        hp = sub.add_parser(helper.name, help=helper.help)
        helper.add_arguments(hp)

    return parser
