---
name: mgs-excel
description: "Excel: Excel workbooks (helpers: +read/+append)."
metadata:
  version: 0.8.2
---

# excel

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

```bash
mgs excel <verb> [flags]
```

## Helper Commands

| Command | Description |
|---------|-------------|
| [`+read`](../mgs-excel-read/SKILL.md) | Read an Excel worksheet range or usedRange |
| [`+append`](../mgs-excel-append/SKILL.md) | Append a row to an Excel table |

## Generic Verbs

| Verb | Description |
|------|-------------|
| `list` | List workbook items |
| `get <id>` | Get one workbook |
| `create --json '{…}'` | Create (POST) |
| `update <id> --json '{…}'` | Update (PATCH) |
| `delete <id>` | Delete |
| `<action> <id> --json '{…}'` | Bound action — see `mgs schema excel` |

## Discovering Commands

```bash
mgs excel --help
mgs schema excel
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
