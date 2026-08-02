---
name: mgs-teams-chats
description: "Teams: List your recent chats (for discovering chat ids)"
metadata:
  version: 0.8.2
---

# teams +chats

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

List your recent chats (for discovering chat ids)

Run `mgs teams +chats --help` for the live flag list.

## Usage

```bash
mgs teams +chats [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--max` | — | 20 | Max chats to return |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs teams +chats [flags]
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-teams](../mgs-teams/SKILL.md) — All teams commands
