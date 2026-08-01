---
name: mgs-mail-read
description: "Mail: Read a message and render clean body/headers"
metadata:
  version: 0.7.1
---

# mail +read

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Read a message and render clean body/headers

Run `mgs mail +read --help` for the live flag list.

## Usage

```bash
mgs mail +read <ID> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `id` | ✓ | — | Message id |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs mail +read <MESSAGE_ID>
```

## Tips

- HTML bodies are rendered to plain text automatically.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-mail](../mgs-mail/SKILL.md) — All mail commands
