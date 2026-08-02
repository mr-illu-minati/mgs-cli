import argparse

from mgs.executor import opts_from_namespace
from mgs.helpers import onenote, registry  # noqa: F401


def _run(verb, args):
    helper = registry.get("onenotePage", verb)
    p = argparse.ArgumentParser()
    helper.add_arguments(p)
    ns = p.parse_args(args)
    return helper.run("", ns, opts_from_namespace(ns))


def test_write_dry_run():
    out = _run("+write", ["--title", "Notes", "--content", "hello", "--dry-run"])
    assert out["method"] == "POST"
    assert out["url"].endswith("/me/onenote/pages")
    assert out["contentType"] == "text/html"
    assert "<title>Notes</title>" in out["html"]


def test_write_dry_run_section():
    out = _run("+write", ["--title", "N", "--content", "x", "--section", "1-abc", "--dry-run"])
    assert out["url"].endswith("/me/onenote/sections/1-abc/pages")


def test_registered():
    assert registry.get("onenotePage", "+write") is not None


def test_write_dry_run_with_mailbox(monkeypatch):
    monkeypatch.setenv("MGS_MAILBOX", "box@contoso.com")
    out = _run("+write", ["--title", "N", "--content", "x", "--dry-run"])
    assert out["url"].endswith("/users/box%40contoso.com/onenote/pages")
