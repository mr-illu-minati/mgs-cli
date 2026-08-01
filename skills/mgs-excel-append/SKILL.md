---
name: mgs-excel-append
description: "Excel: Append a row to an Excel table"
metadata:
  version: 0.7.2
---

# excel +append

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Append a row to an Excel table

Run `mgs excel +append --help` for the live flag list.

## Usage

```bash
mgs excel +append --file <FILE> --values <VALUES> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--file` | ✓ | — | Workbook drive item id or /path |
| `--table` | — | Table1 | Table name |
| `--values` | ✓ | — | Comma-separated cell values |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs excel +append --file /Budget.xlsx --table Table1 --values "Alice,42,3.14"
```

## Tips

- Requires an existing table; numbers are coerced automatically.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-excel](../mgs-excel/SKILL.md) — All excel commands
