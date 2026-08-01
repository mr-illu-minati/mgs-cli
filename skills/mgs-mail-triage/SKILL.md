---
name: mgs-mail-triage
description: "Mail: Summarize unread mail (ranked, compact) for fast scanning"
metadata:
  version: 0.7.1
---

# mail +triage

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Summarize unread mail (ranked, compact) for fast scanning

Run `mgs mail +triage --help` for the live flag list.

## Usage

```bash
mgs mail +triage [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--folder` | — | inbox | Mail folder (wellKnownName or id) |
| `--max` | — | 10 | Max messages to return |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs mail +triage --max 10
mgs mail +triage --folder archive
```

## Tips

- Read-only; returns a ranked summary of unread mail for quick scanning.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-mail](../mgs-mail/SKILL.md) — All mail commands
