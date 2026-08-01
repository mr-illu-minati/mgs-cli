---
name: mgs-mail-reply-all
description: "Mail: Reply-all to a message"
metadata:
  version: 0.7.1
---

# mail +reply-all

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Reply-all to a message

Run `mgs mail +reply-all --help` for the live flag list.

## Usage

```bash
mgs mail +reply-all <ID> [flags]
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
mgs mail +reply-all <ID> [flags]
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-mail](../mgs-mail/SKILL.md) — All mail commands
