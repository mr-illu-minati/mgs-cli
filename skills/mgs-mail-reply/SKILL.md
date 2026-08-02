---
name: mgs-mail-reply
description: "Mail: Reply to a message (threading handled by Graph)"
metadata:
  version: 0.8.1
---

# mail +reply

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Reply to a message (threading handled by Graph)

Run `mgs mail +reply --help` for the live flag list.

## Usage

```bash
mgs mail +reply <ID> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `id` | ✓ | — | Message id |
| `--body` | — | — | Email body |
| `--html` | — | — | Treat body as HTML |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs mail +reply <ID> [flags]
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-mail](../mgs-mail/SKILL.md) — All mail commands
