---
name: mgs-files
description: "Files: Browse and manage OneDrive/SharePoint files."
metadata:
  version: 0.7.2
---

# files

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

```bash
mgs files <verb> [flags]
```

## Helper Commands

| Command | Description |
|---------|-------------|
| [`+upload`](../mgs-files-upload/SKILL.md) | Upload a file (auto small PUT or chunked upload session for >4 MB) |
| [`+download`](../mgs-files-download/SKILL.md) | Download a drive item (by id or /path) to a local file |

## Generic Verbs

| Verb | Description |
|------|-------------|
| `list` | List driveItem items |
| `get <id>` | Get one driveItem |
| `create --json '{…}'` | Create (POST) |
| `update <id> --json '{…}'` | Update (PATCH) |
| `delete <id>` | Delete |
| `<action> <id> --json '{…}'` | Bound action — see `mgs schema files` |

## Discovering Commands

```bash
mgs files --help
mgs schema files
```

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
