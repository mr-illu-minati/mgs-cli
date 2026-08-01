---
name: mgs-mail-watch
description: "Mail: Stream new mail as NDJSON via Graph delta polling"
metadata:
  version: 0.7.1
---

# mail +watch

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Stream new mail as NDJSON via Graph delta polling

Run `mgs mail +watch --help` for the live flag list.

## Usage

```bash
mgs mail +watch [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--folder` | — | inbox | Mail folder (wellKnownName or id) |
| `--interval` | — | 30 | Poll interval in seconds |
| `--max-iterations` | — | 0 | 0 = run until interrupted |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs mail +watch [flags]
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-mail](../mgs-mail/SKILL.md) — All mail commands
