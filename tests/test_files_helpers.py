import argparse

from mgs.executor import opts_from_namespace
from mgs.helpers import files  # noqa: F401  (registers helpers)
from mgs.helpers import registry


def _run(verb, args):
    helper = registry.get("driveItem", verb)
    p = argparse.ArgumentParser()
    helper.add_arguments(p)
    ns = p.parse_args(args)
    return helper.run("", ns, opts_from_namespace(ns))


def test_upload_registered():
    assert registry.get("driveItem", "+upload") is not None


def test_upload_small_dry_run(tmp_path):
    f = tmp_path / "small.txt"
    f.write_bytes(b"hello")
    out = _run("+upload", [str(f), "--to", "/Docs", "--dry-run"])
    assert out["mode"] == "small"
    assert out["method"] == "PUT"
    assert out["url"].endswith("/me/drive/root:/Docs/small.txt:/content")
    assert out["size"] == 5


def test_upload_large_dry_run(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * (5 * 1024 * 1024))  # 5 MB > 4 MB
    out = _run("+upload", [str(f), "--chunk-mb", "5", "--dry-run"])
    assert out["mode"] == "session"
    assert out["method"] == "POST"
    assert out["url"].endswith("/me/drive/root:/big.bin:/createUploadSession")
    assert out["chunks"] == 1  # 5 MB in 5 MB chunks


def test_download_registered():
    assert registry.get("driveItem", "+download") is not None


def test_download_dry_run_by_path():
    out = _run("+download", ["/Reports/Q3.xlsx", "--dry-run"])
    assert out["method"] == "GET"
    # Resolved with a plain GET (no $select), so Graph returns the downloadUrl annotation.
    assert out["url"] == "https://graph.microsoft.com/v1.0/me/drive/root:/Reports/Q3.xlsx:"


def test_download_dry_run_by_id_with_out():
    out = _run("+download", ["01ABC", "--out", "/tmp/x.bin", "--dry-run"])
    assert "/me/drive/items/01ABC" in out["url"]
    assert out["out"] == "/tmp/x.bin"
