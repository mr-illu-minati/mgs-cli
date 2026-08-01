import os

from mgs import skills


def _skill_dirs(p):
    return sorted(d for d in os.listdir(p) if d.startswith("mgs-"))


def test_install_default_targets(tmp_path):
    summary = skills.install(dir=str(tmp_path), targets=["claude", "agents"])
    assert os.path.exists(tmp_path / ".claude" / "skills" / "mgs-mail-send" / "SKILL.md")
    assert os.path.exists(tmp_path / ".agents" / "skills" / "mgs-mail-send" / "SKILL.md")
    # summary reports per-target counts
    assert summary[".claude/skills"]["added"] >= 25
    assert summary[".claude/skills"]["removed"] == 0


def test_install_is_idempotent(tmp_path):
    skills.install(dir=str(tmp_path), targets=["claude"])
    s2 = skills.install(dir=str(tmp_path), targets=["claude"])
    assert s2[".claude/skills"]["added"] == 0
    assert s2[".claude/skills"]["unchanged"] >= 25


def test_install_prune_removes_stale_mgs_skills_only(tmp_path):
    target = tmp_path / ".claude" / "skills"
    # a stale mgs skill from an old version, and a NON-mgs skill that must survive
    (target / "mgs-old-helper").mkdir(parents=True)
    (target / "mgs-old-helper" / "SKILL.md").write_text("stale")
    (target / "my-own-skill").mkdir(parents=True)
    (target / "my-own-skill" / "SKILL.md").write_text("keep me")
    summary = skills.install(dir=str(tmp_path), targets=["claude"], prune=True)
    assert not (target / "mgs-old-helper").exists()      # pruned
    assert (target / "my-own-skill" / "SKILL.md").read_text() == "keep me"  # untouched
    assert summary[".claude/skills"]["removed"] >= 1


def test_install_updates_changed_skill(tmp_path):
    target = tmp_path / ".agents" / "skills"
    (target / "mgs-mail-send").mkdir(parents=True)
    (target / "mgs-mail-send" / "SKILL.md").write_text("old content")
    summary = skills.install(dir=str(tmp_path), targets=["agents"])
    assert summary[".agents/skills"]["updated"] >= 1
    assert "name: mgs-mail-send" in (target / "mgs-mail-send" / "SKILL.md").read_text()
