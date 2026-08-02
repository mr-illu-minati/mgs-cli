---
name: mgs-calendar-insert
description: "Calendar: Create a calendar event (conflict-checked unless --no-conflict-check)"
metadata:
  version: 0.8.1
---

# calendar +insert

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Create a calendar event (conflict-checked unless --no-conflict-check)

Run `mgs calendar +insert --help` for the live flag list.

## Usage

```bash
mgs calendar +insert --start <START> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--subject` | — | — | Event subject |
| `--start` | ✓ | — | ISO start, e.g. 2026-07-01T14:00 |
| `--end` | — | — | ISO end (overrides --duration) |
| `--duration` | — | 30 | Minutes (default 30) |
| `--attendees` | — | — | Comma-separated emails |
| `--location` | — | — | Event location |
| `--body` | — | — | Event body/notes |
| `--all-day` | — | — | Create an all-day event |
| `--online` | — | — | Create a Teams online meeting |
| `--timezone` | — | UTC | IANA timezone (default UTC) |
| `--no-conflict-check` | — | — | Skip the overlap check |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs calendar +insert --subject Sync --start 2026-07-01T14:00 --duration 30 --attendees a@x.com
mgs calendar +insert --subject Review --start 2026-07-01T15:00 --end 2026-07-01T16:00 --online
```

## Tips

- Conflicts are reported (not blocked) unless you pass --no-conflict-check.
- Use --dry-run to preview the event before creating it.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-calendar](../mgs-calendar/SKILL.md) — All calendar commands
