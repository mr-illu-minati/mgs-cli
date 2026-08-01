---
name: mgs-files-download
description: "Files: Download a drive item (by id or /path) to a local file"
metadata:
  version: 0.7.1
---

# files +download

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Download a drive item (by id or /path) to a local file

Run `mgs files +download --help` for the live flag list.

## Usage

```bash
mgs files +download <REF> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `ref` | ✓ | — | Drive item id or /path |
| `--out` | — | — | Local destination (default: the item's name) |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs files +download /Documents/report.pdf
mgs files +download <ITEM_ID> --out ./local.pdf
```

## Tips

- Accepts a drive-item id or a /path.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-files](../mgs-files/SKILL.md) — All files commands
