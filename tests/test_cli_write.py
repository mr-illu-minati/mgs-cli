import json

from mgs.cli import main


def test_update_dry_run(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    assert main(["mail", "update", "AAA", "--json", '{"isRead":true}', "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["method"] == "PATCH"
    assert out["url"].endswith("/me/messages/AAA")
    assert out["body"] == {"isRead": True}


def test_delete_dry_run(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    assert main(["mail", "delete", "AAA", "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["method"] == "DELETE"


def test_bound_action_dry_run_validates_against_metadata(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    # Seed a fresh metadata cache so no network is needed.
    d = tmp_path / "metadata" / "v1"
    (d / "types").mkdir(parents=True)
    (d / "types" / "message.json").write_text(json.dumps(
        {"name": "message", "namespace": "microsoft.graph", "properties": [], "navigations": []}))
    (d / "operations.json").write_text(json.dumps({"message": [{"name": "move", "parameters": []}]}))
    import time
    (d / ".stamp").write_text(str(time.time()))
    assert main(["mail", "move", "AAA", "--json", '{"destinationId":"archive"}', "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["url"].endswith("/me/messages/AAA/move")
    assert out["body"] == {"destinationId": "archive"}


def test_unknown_action_is_usage_error(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    d = tmp_path / "metadata" / "v1"
    (d / "types").mkdir(parents=True)
    (d / "types" / "message.json").write_text(json.dumps(
        {"name": "message", "namespace": "microsoft.graph", "properties": [], "navigations": []}))
    (d / "operations.json").write_text(json.dumps({"message": [{"name": "move", "parameters": []}]}))
    import time
    (d / ".stamp").write_text(str(time.time()))
    assert main(["mail", "bogusaction", "AAA", "--dry-run"]) == 2
    assert "bogusaction" in json.loads(capsys.readouterr().err)["error"]["message"]
