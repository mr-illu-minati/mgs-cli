---
name: mgs-onenote
description: "OneNote: OneNote pages."
metadata:
  version: 0.8.2
---

# onenote

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

```bash
mgs onenote <verb> [flags]
```

## Helper Commands

| Command | Description |
|---------|-------------|
| [`+write`](../mgs-onenote-write/SKILL.md) | Create a OneNote page (--title, --content, [--html], [--section]) |

## Generic Verbs

| Verb | Description |
|------|-------------|
| `list` | List onenotePage items |
| `get <id>` | Get one onenotePage |
| `create --json '{…}'` | Create (POST) |
| `update <id> --json '{…}'` | Update (PATCH) |
| `delete <id>` | Delete |
| `<action> <id> --json '{…}'` | Bound action — see `mgs schema onenote` |

## Discovering Commands

```bash
mgs onenote --help
mgs schema onenote
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
