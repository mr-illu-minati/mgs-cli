import json

from mgs.cli import main


def test_help_returns_zero(capsys):
    assert main(["--help"]) == 0
    out = capsys.readouterr().out
    assert "mail" in out and "users" in out
    assert "skills install" in out  # help lists the skills command
    assert "+helper" in out  # help mentions helper verbs


def test_version_flag(capsys):
    from mgs import __version__

    assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == __version__


def test_auth_status_logged_out(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    assert main(["auth", "status"]) == 0
    assert json.loads(capsys.readouterr().out)["authenticated"] is False


def test_mail_list_dry_run(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    assert main(["mail", "list", "--top", "5", "--select", "subject", "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["dryRun"] is True
    assert out["url"] == "https://graph.microsoft.com/v1.0/me/messages?%24select=subject&%24top=5"


def test_unknown_service_is_usage_error(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    assert main(["nope"]) == 2
    assert json.loads(capsys.readouterr().err)["error"]["kind"] == "usage"


def test_generate_skills(capsys, monkeypatch, tmp_path):
    from mgs.cli import main

    assert main(["generate-skills", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "mgs-shared" in out or "skills" in out
    import os

    assert os.path.exists(tmp_path / "mgs-shared" / "SKILL.md")


def test_skills_install(capsys, monkeypatch, tmp_path):
    from mgs.cli import main

    assert main(["skills", "install", "--dir", str(tmp_path)]) == 0
    import os

    assert os.path.exists(tmp_path / ".claude" / "skills" / "mgs-mail-send" / "SKILL.md")
    assert os.path.exists(tmp_path / ".agents" / "skills" / "mgs-mail-send" / "SKILL.md")
