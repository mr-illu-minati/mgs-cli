---
name: mgs-users
description: "Users: Look up users in the directory."
metadata:
  version: 0.7.1
---

# users

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

```bash
mgs users <verb> [flags]
```

## Generic Verbs

| Verb | Description |
|------|-------------|
| `list` | List user items |
| `get <id>` | Get one user |
| `create --json '{…}'` | Create (POST) |
| `update <id> --json '{…}'` | Update (PATCH) |
| `delete <id>` | Delete |
| `<action> <id> --json '{…}'` | Bound action — see `mgs schema users` |

## Discovering Commands

```bash
mgs users --help
mgs schema users
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
