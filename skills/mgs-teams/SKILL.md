---
name: mgs-teams
description: "Teams: Microsoft Teams: teams, channels, messages."
metadata:
  version: 0.7.1
---

# teams

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

```bash
mgs teams <verb> [flags]
```

## Helper Commands

| Command | Description |
|---------|-------------|
| [`+send`](../mgs-teams-send/SKILL.md) | Send a Teams message to a channel (--team/--channel) or chat (--chat) |
| [`+channels`](../mgs-teams-channels/SKILL.md) | List channels in a team |
| [`+chats`](../mgs-teams-chats/SKILL.md) | List your recent chats (for discovering chat ids) |

## Generic Verbs

| Verb | Description |
|------|-------------|
| `list` | List team items |
| `get <id>` | Get one team |
| `create --json '{…}'` | Create (POST) |
| `update <id> --json '{…}'` | Update (PATCH) |
| `delete <id>` | Delete |
| `<action> <id> --json '{…}'` | Bound action — see `mgs schema teams` |

## Discovering Commands

```bash
mgs teams --help
mgs schema teams
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
