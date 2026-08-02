---
name: mgs-teams-channels
description: "Teams: List channels in a team"
metadata:
  version: 0.8.1
---

# teams +channels

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

List channels in a team

Run `mgs teams +channels --help` for the live flag list.

## Usage

```bash
mgs teams +channels --team <TEAM> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--team` | ✓ | — | Team id |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs teams +channels --team <TEAM> [flags]
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-teams](../mgs-teams/SKILL.md) — All teams commands
