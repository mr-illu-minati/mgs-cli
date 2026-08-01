---
name: mgs-mail-forward
description: "Mail: Forward a message to new recipients"
metadata:
  version: 0.7.1
---

# mail +forward

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Forward a message to new recipients

Run `mgs mail +forward --help` for the live flag list.

## Usage

```bash
mgs mail +forward <ID> --to <TO> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `id` | ✓ | — | Message id |
| `--to` | ✓ | — | Recipient(s), comma-separated |
| `--cc` | — | — | CC recipient(s), comma-separated |
| `--comment` | — | — | Text to include with the forward |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs mail +forward <ID> --to <TO> [flags]
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-mail](../mgs-mail/SKILL.md) — All mail commands
