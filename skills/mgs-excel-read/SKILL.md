---
name: mgs-excel-read
description: "Excel: Read an Excel worksheet range or usedRange"
metadata:
  version: 0.7.2
---

# excel +read

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Read an Excel worksheet range or usedRange

Run `mgs excel +read --help` for the live flag list.

## Usage

```bash
mgs excel +read --file <FILE> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--file` | ✓ | — | Workbook drive item id or /path |
| `--sheet` | — | Sheet1 | Worksheet name |
| `--range` | — | — | A1 address, e.g. A1:C10 (default: usedRange) |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs excel +read --file /Budget.xlsx --sheet Sheet1 --range "A1:C10"
mgs excel +read --file <ITEM_ID> --sheet Sheet1
```

## Tips

- Omit --range to read the whole usedRange.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-excel](../mgs-excel/SKILL.md) — All excel commands
