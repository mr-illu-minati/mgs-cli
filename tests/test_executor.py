import argparse

import pytest

from mgs.errors import ValidationError
from mgs.executor import build_plan, execute, opts_from_namespace
from mgs.services import resolve


def _opts(**kw):
    ns = argparse.Namespace(
        select=None,
        filter=None,
        orderby=None,
        expand=None,
        top=None,
        skip=None,
        page_all=False,
        dry_run=False,
        beta=False,
    )
    for k, v in kw.items():
        setattr(ns, k, v)
    return opts_from_namespace(ns)


def test_list_plan_uses_root_path_and_query():
    plan = build_plan(resolve("mail"), "list", None, _opts(select="subject", top=3))
    assert plan.method == "GET"
    assert plan.path == "/me/messages"
    assert "%24select=subject" in plan.query
    assert "%24top=3" in plan.query


def test_get_plan_appends_encoded_id():
    plan = build_plan(resolve("users"), "get", "john doe", _opts())
    assert plan.path == "/users/john%20doe"


def test_get_plan_rejects_traversal():
    with pytest.raises(ValidationError):
        build_plan(resolve("users"), "get", "../secrets", _opts())


def test_execute_dry_run_builds_url_without_network():
    plan = build_plan(resolve("mail"), "list", None, _opts(top=5, dry_run=True))
    out = execute(plan, _opts(top=5, dry_run=True), token="")
    assert out["dryRun"] is True
    assert out["url"] == "https://graph.microsoft.com/v1.0/me/messages?%24top=5"
