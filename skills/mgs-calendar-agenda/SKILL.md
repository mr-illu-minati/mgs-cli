---
name: mgs-calendar-agenda
description: "Calendar: Show upcoming events (calendarView; expands recurrences)"
metadata:
  version: 0.8.1
---

# calendar +agenda

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Show upcoming events (calendarView; expands recurrences)

Run `mgs calendar +agenda --help` for the live flag list.

## Usage

```bash
mgs calendar +agenda [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--start` | — | — | Window start date YYYY-MM-DD (default: today) |
| `--days` | — | 1 | Days to show (default 1 = today) |
| `--week` | — | — | Show the next 7 days |
| `--timezone` | — | UTC | IANA timezone (default UTC) |
| `--max` | — | 50 | Max events to return |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs calendar +agenda --week --timezone America/Toronto
mgs calendar +agenda --start 2026-07-01 --days 1
```

## Tips

- Uses calendarView, so recurring events are expanded into instances.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-calendar](../mgs-calendar/SKILL.md) — All calendar commands
