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


def test_mail_list_dry_run_with_mailbox_flag(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    assert main(["mail", "list", "--top", "5", "--mailbox", "box@contoso.com", "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["url"] == (
        "https://graph.microsoft.com/v1.0/users/box%40contoso.com/messages?%24top=5"
    )


def test_mailbox_flag_equals_form(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    assert main(["mail", "list", "--mailbox=box@contoso.com", "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert "/users/box%40contoso.com/messages" in out["url"]


def test_mailbox_flag_without_value_is_usage_error(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    assert main(["mail", "list", "--dry-run", "--mailbox"]) == 2
    assert json.loads(capsys.readouterr().err)["error"]["kind"] == "usage"


def test_mailbox_flag_does_not_leak_between_runs(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    assert main(["mail", "list", "--mailbox", "box@contoso.com", "--dry-run"]) == 0
    capsys.readouterr()
    assert main(["mail", "list", "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert "/me/messages" in out["url"]


def test_app_only_without_mailbox_is_explicit_usage_error(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("MGS_AUTH", "app-only")
    monkeypatch.delenv("MGS_MAILBOX", raising=False)
    monkeypatch.delenv("MGS_DEFAULT_MAILBOX", raising=False)
    assert main(["mail", "list", "--dry-run"]) == 2
    err = json.loads(capsys.readouterr().err)["error"]
    assert err["kind"] == "usage"
    assert "--mailbox" in err["message"] or "MGS_DEFAULT_MAILBOX" in err["message"]


def test_app_only_with_default_mailbox_dry_run(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MGS_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("MGS_AUTH", "app-only")
    monkeypatch.delenv("MGS_MAILBOX", raising=False)
    monkeypatch.setenv("MGS_DEFAULT_MAILBOX", "sandbox-cabinet@contoso.com")
    assert main(["mail", "list", "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert "/users/sandbox-cabinet%40contoso.com/messages" in out["url"]


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
