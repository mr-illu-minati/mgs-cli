---
name: mgs-calendar
description: "Calendar: Manage Outlook calendar events."
metadata:
  version: 0.8.2
---

# calendar

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

```bash
mgs calendar <verb> [flags]
```

## Helper Commands

| Command | Description |
|---------|-------------|
| [`+agenda`](../mgs-calendar-agenda/SKILL.md) | Show upcoming events (calendarView; expands recurrences) |
| [`+insert`](../mgs-calendar-insert/SKILL.md) | Create a calendar event (conflict-checked unless --no-conflict-check) |

## Generic Verbs

| Verb | Description |
|------|-------------|
| `list` | List event items |
| `get <id>` | Get one event |
| `create --json '{…}'` | Create (POST) |
| `update <id> --json '{…}'` | Update (PATCH) |
| `delete <id>` | Delete |
| `<action> <id> --json '{…}'` | Bound action — see `mgs schema calendar` |

## Discovering Commands

```bash
mgs calendar --help
mgs schema calendar
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
