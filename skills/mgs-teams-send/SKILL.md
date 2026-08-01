---
name: mgs-teams-send
description: "Teams: Send a Teams message to a channel (--team/--channel) or chat (--chat)"
metadata:
  version: 0.7.1
---

# teams +send

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Send a Teams message to a channel (--team/--channel) or chat (--chat)

Run `mgs teams +send --help` for the live flag list.

## Usage

```bash
mgs teams +send --message <MESSAGE> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--team` | — | — | Team id |
| `--channel` | — | — | Channel id |
| `--chat` | — | — | Chat id |
| `--message` | ✓ | — | Message text |
| `--html` | — | — | Treat message as HTML |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs teams +send --team <TEAM_ID> --channel <CHANNEL_ID> --message 'Deploy done'
mgs teams +send --chat <CHAT_ID> --message 'hi' --html
```

## Tips

- Discover ids with `mgs teams list`, `mgs teams +channels --team <id>`, `mgs teams +chats`.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-teams](../mgs-teams/SKILL.md) — All teams commands
