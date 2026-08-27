---
name: mgs-mail-attachments
description: "Mail: List a message's attachments; --download DIR saves file attachments"
metadata:
  version: 0.8.3
---

# mail +attachments

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

List a message's attachments; --download DIR saves file attachments

Run `mgs mail +attachments --help` for the live flag list.

## Usage

```bash
mgs mail +attachments <ID> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `id` | ✓ | — | Message id |
| `--download` | — | — | Save file attachments into DIR |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs mail +attachments <ID> [flags]
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-mail](../mgs-mail/SKILL.md) — All mail commands
