import os

from mgs import skills
from mgs.helpers import registry


def test_flag_rows_for_send():
    helper = registry.get("message", "+send")
    rows = skills._flag_rows(helper)
    flags = [r[0] for r in rows]
    assert "`--to`" in flags
    assert "`--subject`" in flags
    assert "`--dry-run`" in flags


def test_generate_writes_expected_tree(tmp_path):
    written = skills.generate(out_dir=str(tmp_path))
    # shared, a service, a helper, and the index all exist
    assert os.path.exists(tmp_path / "mgs-shared" / "SKILL.md")
    assert os.path.exists(tmp_path / "mgs-mail" / "SKILL.md")
    assert os.path.exists(tmp_path / "mgs-mail-send" / "SKILL.md")
    assert os.path.exists(tmp_path / "mgs-calendar-agenda" / "SKILL.md")
    assert os.path.exists(tmp_path / "mgs-teams-send" / "SKILL.md")
    assert os.path.exists(tmp_path / "SKILLS.md")
    assert os.path.exists(tmp_path / "AGENTS.md")  # agent-agnostic entry point
    assert len(written) >= 27  # 1 shared + 7 services + 17 helpers + index + AGENTS.md


def test_agents_md_is_agent_agnostic(tmp_path):
    skills.generate(out_dir=str(tmp_path))
    md = (tmp_path / "AGENTS.md").read_text()
    assert "mgs <service> <verb>" in md
    assert "--dry-run" in md
    assert "mgs mail +send" in md  # services + helpers catalogued


def test_helper_skill_content(tmp_path):
    skills.generate(out_dir=str(tmp_path))
    md = (tmp_path / "mgs-mail-send" / "SKILL.md").read_text()
    assert "name: mgs-mail-send" in md
    assert "description:" in md
    assert "openclaw" not in md
    assert "cliHelp" not in md
    assert "Run `mgs" in md  # cliHelp hint moved into body
    assert "## Flags" in md
    assert "## Usage" in md
    assert "mgs-shared/SKILL.md" in md  # see-also link


def test_service_skill_lists_helpers(tmp_path):
    skills.generate(out_dir=str(tmp_path))
    md = (tmp_path / "mgs-mail" / "SKILL.md").read_text()
    assert "## Helper Commands" in md
    assert "+send" in md and "+triage" in md
    assert "mgs schema mail" in md


def test_filter_limits_output(tmp_path):
    written = skills.generate(out_dir=str(tmp_path), filter="mail")
    assert all("mail" in os.path.basename(os.path.dirname(p)) or p.endswith("SKILLS.md") is False
               for p in written)
    assert any("mgs-mail-send" in p for p in written)
    assert not os.path.exists(tmp_path / "mgs-calendar" / "SKILL.md")
