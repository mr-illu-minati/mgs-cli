import argparse

from mgs.executor import opts_from_namespace
from mgs.helpers import excel, registry  # noqa: F401


def _run(verb, args):
    helper = registry.get("workbook", verb)
    p = argparse.ArgumentParser()
    helper.add_arguments(p)
    ns = p.parse_args(args)
    return helper.run("", ns, opts_from_namespace(ns))


def test_read_dry_run_usedrange():
    out = _run("+read", ["--file", "01ABC", "--sheet", "Sheet1", "--dry-run"])
    assert out["method"] == "GET"
    assert out["url"].endswith("/workbook/worksheets('Sheet1')/usedRange")


def test_read_dry_run_range():
    out = _run(
        "+read", ["--file", "/Book.xlsx", "--sheet", "Sheet1", "--range", "A1:B2", "--dry-run"]
    )
    assert "range(address='A1%3AB2')" in out["url"]


def test_append_dry_run():
    out = _run(
        "+append", ["--file", "01ABC", "--table", "Table1", "--values", "a,1,2.5", "--dry-run"]
    )
    assert out["method"] == "POST"
    assert out["url"].endswith("/workbook/tables/Table1/rows/add")
    assert out["body"] == {"values": [["a", 1, 2.5]]}


def test_registered():
    assert registry.get("workbook", "+read") is not None
    assert registry.get("workbook", "+append") is not None
