---
name: mgs-mail
description: "Mail: Read, send, and manage Outlook mail."
metadata:
  version: 0.8.1
---

# mail

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

```bash
mgs mail <verb> [flags]
```

## Helper Commands

| Command | Description |
|---------|-------------|
| [`+send`](../mgs-mail-send/SKILL.md) | Send an email (--to/--cc/--bcc --subject --body [--html] [--attach] [--draft]) |
| [`+read`](../mgs-mail-read/SKILL.md) | Read a message and render clean body/headers |
| [`+reply`](../mgs-mail-reply/SKILL.md) | Reply to a message (threading handled by Graph) |
| [`+reply-all`](../mgs-mail-reply-all/SKILL.md) | Reply-all to a message |
| [`+forward`](../mgs-mail-forward/SKILL.md) | Forward a message to new recipients |
| [`+triage`](../mgs-mail-triage/SKILL.md) | Summarize unread mail (ranked, compact) for fast scanning |
| [`+watch`](../mgs-mail-watch/SKILL.md) | Stream new mail as NDJSON via Graph delta polling |

## Generic Verbs

| Verb | Description |
|------|-------------|
| `list` | List message items |
| `get <id>` | Get one message |
| `create --json '{…}'` | Create (POST) |
| `update <id> --json '{…}'` | Update (PATCH) |
| `delete <id>` | Delete |
| `<action> <id> --json '{…}'` | Bound action — see `mgs schema mail` |

## Discovering Commands

```bash
mgs mail --help
mgs schema mail
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
