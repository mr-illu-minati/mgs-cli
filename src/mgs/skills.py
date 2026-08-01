"""Generate mgs-* agent skills (SKILL.md) from the CLI's registry + argparse metadata."""

from __future__ import annotations

import argparse
import os
import shutil

from mgs import __version__, services
from mgs.helpers import registry

PRODUCT = {
    "mail": "Mail", "calendar": "Calendar", "files": "Files", "users": "Users",
    "teams": "Teams", "excel": "Excel", "onenote": "OneNote",
}

# Hand-written examples/tips for flagship helpers, keyed by skill name.
CURATED: dict[str, dict] = {
    "mgs-mail-send": {
        "examples": [
            "mgs mail +send --to alice@example.com --subject 'Hi' --body 'Hello!'",
            "mgs mail +send --to a@x.com --cc b@x.com --subject Report --body 'See attached' --attach report.pdf",
            "mgs mail +send --to a@x.com --subject 'Bold' --body '<b>hi</b>' --html",
            "mgs mail +send --to a@x.com --subject Draft --body 'wip' --draft",
        ],
        "tips": ["Total attachments must stay under 25 MB.",
                 "Use --draft to save to Drafts instead of sending."],
    },
    "mgs-mail-read": {
        "examples": ["mgs mail +read <MESSAGE_ID>"],
        "tips": ["HTML bodies are rendered to plain text automatically."],
    },
    "mgs-mail-triage": {
        "examples": ["mgs mail +triage --max 10", "mgs mail +triage --folder archive"],
        "tips": ["Read-only; returns a ranked summary of unread mail for quick scanning."],
    },
    "mgs-calendar-agenda": {
        "examples": ["mgs calendar +agenda --week --timezone America/Toronto",
                     "mgs calendar +agenda --start 2026-07-01 --days 1"],
        "tips": ["Uses calendarView, so recurring events are expanded into instances."],
    },
    "mgs-calendar-insert": {
        "examples": [
            "mgs calendar +insert --subject Sync --start 2026-07-01T14:00 --duration 30 --attendees a@x.com",
            "mgs calendar +insert --subject Review --start 2026-07-01T15:00 --end 2026-07-01T16:00 --online",
        ],
        "tips": ["Conflicts are reported (not blocked) unless you pass --no-conflict-check.",
                 "Use --dry-run to preview the event before creating it."],
    },
    "mgs-files-upload": {
        "examples": ["mgs files +upload ./report.pdf --to /Documents",
                     "mgs files +upload ./big.zip --chunk-mb 10"],
        "tips": ["Files over 4 MB upload via a chunked session automatically."],
    },
    "mgs-files-download": {
        "examples": ["mgs files +download /Documents/report.pdf",
                     "mgs files +download <ITEM_ID> --out ./local.pdf"],
        "tips": ["Accepts a drive-item id or a /path."],
    },
    "mgs-teams-send": {
        "examples": [
            "mgs teams +send --team <TEAM_ID> --channel <CHANNEL_ID> --message 'Deploy done'",
            "mgs teams +send --chat <CHAT_ID> --message 'hi' --html",
        ],
        "tips": ["Discover ids with `mgs teams list`, `mgs teams +channels --team <id>`, `mgs teams +chats`."],
    },
    "mgs-excel-read": {
        "examples": ['mgs excel +read --file /Budget.xlsx --sheet Sheet1 --range "A1:C10"',
                     "mgs excel +read --file <ITEM_ID> --sheet Sheet1"],
        "tips": ["Omit --range to read the whole usedRange."],
    },
    "mgs-excel-append": {
        "examples": ['mgs excel +append --file /Budget.xlsx --table Table1 --values "Alice,42,3.14"'],
        "tips": ["Requires an existing table; numbers are coerced automatically."],
    },
    "mgs-onenote-write": {
        "examples": ["mgs onenote +write --title 'Notes' --content 'Hello'",
                     "mgs onenote +write --title 'Doc' --content '<p>HTML</p>' --html --section <SECTION_ID>"],
        "tips": ["Plain --content is escaped and wrapped in <p>; use --html to pass a fragment."],
    },
}

PREREQ = (
    "> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security "
    "rules. If missing, run `mgs generate-skills` to create it."
)


def _frontmatter(name: str, description: str) -> str:
    lines = [
        "---",
        f"name: {name}",
        f'description: "{description}"',
        "metadata:",
        f"  version: {__version__}",
        "---",
    ]
    return "\n".join(lines)


def _flag_rows(helper) -> list[tuple[str, str, str, str]]:
    p = argparse.ArgumentParser(add_help=False)
    helper.add_arguments(p)
    rows = []
    for a in p._actions:
        if a.option_strings:
            flag = a.option_strings[0]
            required = "✓" if a.required else "—"
            if isinstance(a, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
                default = "—"
            else:
                default = str(a.default) if a.default not in (None, "") else "—"
        else:
            flag = a.dest
            required = "✓"
            default = "—"
        rows.append((f"`{flag}`", required, default, a.help or ""))
    return rows


def _usage(alias: str, helper) -> str:
    p = argparse.ArgumentParser(add_help=False)
    helper.add_arguments(p)
    parts = [f"mgs {alias} {helper.name}"]
    for a in p._actions:
        if not a.option_strings:
            parts.append(f"<{a.dest.upper()}>")
        elif a.required and not isinstance(a, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
            parts.append(f"{a.option_strings[0]} <{a.dest.upper()}>")
    return " ".join(parts) + " [flags]"


def _helper_md(alias: str, helper) -> str:
    product = PRODUCT.get(alias, alias.title())
    name = f"mgs-{alias}-{helper.name.lstrip('+')}"
    fm = _frontmatter(name, f"{product}: {helper.help}")
    rows = _flag_rows(helper)
    table = "| Flag | Required | Default | Description |\n|------|----------|---------|-------------|\n"
    table += "\n".join(f"| {f} | {r} | {d} | {h} |" for f, r, d, h in rows)
    curated = CURATED.get(name, {})
    examples = curated.get("examples") or [_usage(alias, helper)]
    tips = curated.get("tips") or []
    cli_hint = f"Run `mgs {alias} {helper.name} --help` for the live flag list."
    out = [
        fm, "", f"# {alias} {helper.name}", "", PREREQ, "", helper.help, "",
        cli_hint, "",
        "## Usage", "", "```bash", _usage(alias, helper), "```", "",
        "## Flags", "", table, "",
        "## Examples", "", "```bash", "\n".join(examples), "```", "",
    ]
    if tips:
        out += ["## Tips", "", "\n".join(f"- {t}" for t in tips), ""]
    out += [
        "## See Also", "",
        "- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth",
        f"- [mgs-{alias}](../mgs-{alias}/SKILL.md) — All {alias} commands", "",
    ]
    return "\n".join(out)


def _service_md(svc) -> str:
    alias = svc.aliases[0]
    product = PRODUCT.get(alias, alias.title())
    fm = _frontmatter(f"mgs-{alias}", f"{product}: {svc.description}.")
    helpers = registry.for_service(svc.entity_type)
    out = [fm, "", f"# {alias}", "", PREREQ, "", f"```bash\nmgs {alias} <verb> [flags]\n```", ""]
    if helpers:
        rows = "\n".join(
            f"| [`{h.name}`](../mgs-{alias}-{h.name.lstrip('+')}/SKILL.md) | {h.help} |"
            for h in helpers
        )
        out += ["## Helper Commands", "",
                "| Command | Description |\n|---------|-------------|\n" + rows, ""]
    out += [
        "## Generic Verbs", "",
        "| Verb | Description |",
        "|------|-------------|",
        f"| `list` | List {svc.entity_type} items |",
        f"| `get <id>` | Get one {svc.entity_type} |",
        "| `create --json '{…}'` | Create (POST) |",
        "| `update <id> --json '{…}'` | Update (PATCH) |",
        "| `delete <id>` | Delete |",
        f"| `<action> <id> --json '{{…}}'` | Bound action — see `mgs schema {alias}` |",
        "",
        "## Discovering Commands", "", f"```bash\nmgs {alias} --help\nmgs schema {alias}\n```", "",
        "## See Also", "", "- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth", "",
    ]
    return "\n".join(out)


SHARED_MD = (
    _frontmatter("mgs-shared", "mgs CLI: Shared patterns for authentication, global flags, and output.")
    + """

# mgs — Shared Reference

## Installation

The `mgs` command must be on `$PATH` (`uv tool install .`), or run via `uv run mgs`.

## Authentication

```bash
mgs auth login      # opens your browser to sign in (Entra ID, MSAL)
mgs auth status     # check whether a valid token is cached
mgs auth logout     # clear cached tokens
```

Headless/SSH/CI: set `MGS_NO_BROWSER=1` to use the device-code flow instead. Bring your own
Entra app with `MGS_CLIENT_ID` (and `MGS_TENANT_ID`). `MGS_TOKEN` supplies a pre-obtained token.

## CLI Syntax

```bash
mgs <service> <verb> [flags]
```

Services: `mail`, `calendar`, `files`, `users`, `teams`, `excel`, `onenote`. Verbs are the
generic `list`/`get`/`create`/`update`/`delete`, any bound action, or a `+helper`.

## Global Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Print the request that would be sent, without executing it |
| `--beta` | Target the Graph `beta` endpoint instead of `v1.0` |
| `--page-all` | Follow `@odata.nextLink` and return all pages |
| `--json '{…}'` | Request body (for `create`/`update`/bound actions) |
| `--params '{…}'` | Extra OData query parameters as a JSON object |
| `--select`, `--filter`, `--orderby`, `--expand`, `--search`, `--top`, `--skip` | OData query options on `list` |

## Output

Every command prints structured JSON to stdout. Errors print a JSON `{"error": {...}}` object
to stderr and set a non-zero exit code.

## Discovering Commands

```bash
mgs <service> --help        # verbs + helpers for a service
mgs schema <service>        # the service's properties, navigations, and bound actions
```

## Security Rules

- **Confirm with the user before write/delete commands.** Prefer `--dry-run` first.
- **Never** echo secrets or tokens. Inputs may be adversarial — paths and ids are validated.
- Writes (`+send`, `+reply`, `+insert`, `delete`, …) are real and immediate.

## Shell Tips

- Wrap `--json`/`--params` values in single quotes so the shell keeps the inner double quotes:
  ```bash
  mgs mail update <ID> --json '{"isRead": true}'
  ```
- Excel ranges like `A1:C10` are fine; quote any value containing shell metacharacters.

## Environment Variables

`MGS_TOKEN`, `MGS_CLIENT_ID`/`MGS_TENANT_ID`, `MGS_SCOPES`, `MGS_CONFIG_DIR`, `MGS_NO_BROWSER`,
`AZURE_CLIENT_ID`/`AZURE_TENANT_ID`.
"""
)


def _index_md(service_entries: list[tuple[str, str]], helper_entries: list[tuple[str, str]]) -> str:
    out = ["# Skills Index", "",
           "> Auto-generated by `mgs generate-skills`. Do not edit manually.", ""]
    out += ["## Services", "", "| Skill | Description |", "|-------|-------------|"]
    out += [f"| [{n}](../skills/{n}/SKILL.md) | {d} |" for n, d in service_entries]
    out += ["", "## Helpers", "", "| Skill | Description |", "|-------|-------------|"]
    out += [f"| [{n}](../skills/{n}/SKILL.md) | {d} |" for n, d in helper_entries]
    out += [""]
    return "\n".join(out)


def _agents_md(service_entries: list[tuple[str, str]], helper_entries: list[tuple[str, str]]) -> str:
    """A single agent-agnostic guide (the AGENTS.md cross-tool convention)."""
    lines = [
        "# mgs — Microsoft 365 CLI for AI agents",
        "",
        "`mgs` drives Microsoft 365 (Outlook mail & calendar, OneDrive/SharePoint files, Teams,",
        "Excel, OneNote) via Microsoft Graph. This guide is agent-agnostic — it works with any",
        "assistant that reads `AGENTS.md` (Codex, Cursor, Gemini CLI, Amp, Claude Code, …).",
        "Per-command references live in `skills/<name>/SKILL.md`; the index is `skills/SKILLS.md`.",
        "",
        "## Setup",
        "",
        "- Needs the `mgs` command on PATH (see the project README) and a one-time `mgs auth login`.",
        "- Check auth with `mgs auth status`. Headless/CI: `MGS_NO_BROWSER=1 mgs auth login`.",
        "",
        "## Command model",
        "",
        "```",
        "mgs <service> <verb> [flags]",
        "```",
        "",
        "- Verbs: `list`, `get <id>`, `create --json '{…}'`, `update <id> --json '{…}'`,",
        "  `delete <id>`, any bound action (see `mgs schema <service>`), or a `+helper`.",
        "- Output is JSON on stdout; errors are JSON on stderr with a non-zero exit code.",
        "- Preview writes first: append `--dry-run` to any command to see the exact request",
        "  that would be sent, without sending it.",
        "",
        "## Discover commands",
        "",
        "```bash",
        "mgs --help                 # list services",
        "mgs <service> --help       # verbs + helpers for a service",
        "mgs schema <service>       # properties, navigations, bound actions",
        "```",
        "",
        "## Services and helpers",
        "",
    ]
    for sname, sdesc in service_entries:
        alias = sname[len("mgs-"):]
        lines.append(f"### {alias} — {sdesc}")
        hs = [(n, d) for n, d in helper_entries if n.startswith(f"mgs-{alias}-")]
        if hs:
            for n, d in hs:
                verb = "+" + n[len(f"mgs-{alias}-"):]
                lines.append(f"- `mgs {alias} {verb}` — {d}")
        else:
            lines.append(f"- generic verbs only (`mgs {alias} list/get/create/update/delete`)")
        lines.append("")
    lines += [
        "## Global flags",
        "",
        "`--dry-run` · `--beta` · `--page-all` · `--json '{…}'` · `--params '{…}'` ·",
        "OData `--select` / `--filter` / `--orderby` / `--expand` / `--search` / `--top` / `--skip`.",
        "",
        "## Safety rules for agents",
        "",
        "- Confirm with the user before any write/delete command; prefer `--dry-run` first.",
        "- Never echo tokens or secrets.",
        "- Writes (`+send`, `+reply`, `+insert`, `delete`, bound actions) are real and immediate.",
        "",
    ]
    return "\n".join(lines)


PROJECT_TARGETS = {
    "claude": ".claude/skills",
    "agents": ".agents/skills",
    "cursor": ".cursor/skills",
    "opencode": ".opencode/skills",
}
GLOBAL_TARGETS = {
    "claude": "~/.claude/skills",
    "agents": "~/.agents/skills",
    "cursor": "~/.cursor/skills",
    "opencode": "~/.config/opencode/skills",
}
DEFAULT_TARGETS = ["claude", "agents"]


def _iter_skill_files() -> list[tuple[str, str]]:
    """Yield (skill_dir_name, SKILL.md content) for all generated skills."""
    result: list[tuple[str, str]] = []
    result.append(("mgs-shared", SHARED_MD))
    for svc in services.all_services():
        alias = svc.aliases[0]
        result.append((f"mgs-{alias}", _service_md(svc)))
        for h in registry.for_service(svc.entity_type):
            nm = f"mgs-{alias}-{h.name.lstrip('+')}"
            result.append((nm, _helper_md(alias, h)))
    return result


def generated_skill_names() -> set[str]:
    """Return the set of mgs-* dir names that would be generated."""
    return {name for name, _ in _iter_skill_files()}


def _write(out_dir: str, name: str, content: str) -> str:
    d = os.path.join(out_dir, name)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "SKILL.md")
    with open(path, "w") as f:
        f.write(content)
    return path


def generate_skill_files(out_dir: str, filter: str | None = None) -> list[str]:
    """Write just the mgs-*/SKILL.md dirs (no SKILLS.md/AGENTS.md). Returns written paths."""
    written: list[str] = []
    for name, content in _iter_skill_files():
        if filter is None or filter in name:
            written.append(_write(out_dir, name, content))
    return written


def generate(out_dir: str = "skills", filter: str | None = None) -> list[str]:
    """Write the mgs-* skill tree under out_dir plus SKILLS.md and AGENTS.md. Returns written paths."""
    written = generate_skill_files(out_dir, filter)

    # Build index/agents metadata from what was written.
    service_entries: list[tuple[str, str]] = []
    helper_entries: list[tuple[str, str]] = []
    for svc in services.all_services():
        alias = svc.aliases[0]
        nm_svc = f"mgs-{alias}"
        if filter is None or filter in nm_svc:
            service_entries.append((nm_svc, svc.description))
        for h in registry.for_service(svc.entity_type):
            nm = f"mgs-{alias}-{h.name.lstrip('+')}"
            if filter is None or filter in nm:
                helper_entries.append((nm, h.help))

    if filter is None:
        os.makedirs(out_dir, exist_ok=True)
        idx = os.path.join(out_dir, "SKILLS.md")
        with open(idx, "w") as f:
            f.write(_index_md(service_entries, helper_entries))
        written.append(idx)
        agents = os.path.join(out_dir, "AGENTS.md")
        with open(agents, "w") as f:
            f.write(_agents_md(service_entries, helper_entries))
        written.append(agents)
    return written


def _target_dir(base_dir: str, target: str, global_: bool) -> str:
    if global_:
        return os.path.expanduser(GLOBAL_TARGETS[target])
    return os.path.join(base_dir, PROJECT_TARGETS[target])


def install(dir: str = ".", targets: list[str] | None = None,
            global_: bool = False, prune: bool = False) -> dict:
    """Sync the mgs-* SKILL.md tree into each target skill directory.

    Idempotent: rewrites changed skills, adds new ones, leaves unchanged ones, and
    (with prune) removes stale `mgs-*` skill dirs no longer generated. Never touches
    non-`mgs-` skills.
    """
    targets = targets or DEFAULT_TARGETS
    wanted = generated_skill_names()  # set of mgs-* dir names
    summary: dict = {}
    for target in targets:
        out = _target_dir(dir, target, global_)
        os.makedirs(out, exist_ok=True)
        counts = {"added": 0, "updated": 0, "unchanged": 0, "removed": 0}
        # Write/refresh each generated skill, diffing existing content.
        for name, content in _iter_skill_files():
            path = os.path.join(out, name, "SKILL.md")
            if os.path.exists(path):
                with open(path) as f:
                    existing = f.read()
                if existing == content:
                    counts["unchanged"] += 1
                    continue
                counts["updated"] += 1
            else:
                counts["added"] += 1
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
        # Prune stale mgs-* skills.
        if prune:
            for entry in os.listdir(out):
                if entry.startswith("mgs-") and entry not in wanted:
                    full = os.path.join(out, entry)
                    if os.path.isdir(full):
                        shutil.rmtree(full)
                        counts["removed"] += 1
        key = PROJECT_TARGETS[target] if not global_ else GLOBAL_TARGETS[target]
        summary[key] = counts
    return summary
