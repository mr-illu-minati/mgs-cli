import argparse

from mgs.executor import build_plan, opts_from_namespace
from mgs.services import resolve


def _opts(**kw):
    ns = argparse.Namespace(
        select=None, filter=None, orderby=None, expand=None, search=None, top=None, skip=None,
        page_all=False, dry_run=False, beta=False, json=None, params=None, folder=None,
    )
    for k, v in kw.items():
        setattr(ns, k, v)
    return opts_from_namespace(ns)


def test_files_get_by_id_uses_items():
    plan = build_plan(resolve("files"), "get", "01ABC", _opts())
    assert plan.path == "/me/drive/items/01ABC"


def test_files_get_by_path():
    plan = build_plan(resolve("files"), "get", "/Reports/Q3.xlsx", _opts())
    assert plan.path == "/me/drive/root:/Reports/Q3.xlsx:"


def test_files_delete_by_id_uses_items():
    plan = build_plan(resolve("files"), "delete", "01ABC", _opts())
    assert plan.method == "DELETE"
    assert plan.path == "/me/drive/items/01ABC"


def test_files_list_unchanged():
    plan = build_plan(resolve("files"), "list", None, _opts())
    assert plan.path == "/me/drive/root/children"
