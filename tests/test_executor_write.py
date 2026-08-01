import argparse

import pytest

from mgs.errors import UsageError
from mgs.executor import build_plan, execute, opts_from_namespace
from mgs.services import resolve


def _opts(**kw):
    ns = argparse.Namespace(
        select=None, filter=None, orderby=None, expand=None, search=None,
        top=None, skip=None, page_all=False, dry_run=False, beta=False,
        json=None, params=None, folder=None,
    )
    for k, v in kw.items():
        setattr(ns, k, v)
    return opts_from_namespace(ns)


def test_create_plan_posts_root_with_body():
    plan = build_plan(resolve("mail"), "create", None, _opts(json='{"subject":"hi"}'))
    assert plan.method == "POST"
    assert plan.path == "/me/messages"
    assert plan.body == {"subject": "hi"}


def test_update_plan_patches_with_id_and_body():
    plan = build_plan(resolve("mail"), "update", "AAA", _opts(json='{"isRead":true}'))
    assert plan.method == "PATCH"
    assert plan.path == "/me/messages/AAA"
    assert plan.body == {"isRead": True}


def test_delete_plan():
    plan = build_plan(resolve("mail"), "delete", "AAA", _opts())
    assert plan.method == "DELETE"
    assert plan.path == "/me/messages/AAA"
    assert plan.body is None


def test_bound_action_plan_posts_id_action():
    plan = build_plan(resolve("mail"), "move", "AAA", _opts(json='{"destinationId":"archive"}'))
    assert plan.method == "POST"
    assert plan.path == "/me/messages/AAA/move"
    assert plan.body == {"destinationId": "archive"}


def test_list_folder_scoping_and_search():
    plan = build_plan(resolve("mail"), "list", None, _opts(folder="inbox", search='"budget"'))
    assert plan.path == "/me/mailFolders/inbox/messages"
    assert "%24search=%22budget%22" in plan.query


def test_params_merged_into_query():
    plan = build_plan(resolve("mail"), "list", None, _opts(params='{"$count":"true"}'))
    assert "%24count=true" in plan.query


def test_invalid_json_is_usage_error():
    with pytest.raises(UsageError):
        build_plan(resolve("mail"), "create", None, _opts(json="{not json"))


def test_dry_run_includes_body():
    plan = build_plan(resolve("mail"), "create", None, _opts(json='{"a":1}', dry_run=True))
    out = execute(plan, _opts(json='{"a":1}', dry_run=True), token="")
    assert out["dryRun"] is True
    assert out["method"] == "POST"
    assert out["body"] == {"a": 1}
