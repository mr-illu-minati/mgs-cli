---
name: mgs-files-upload
description: "Files: Upload a file (auto small PUT or chunked upload session for >4 MB)"
metadata:
  version: 0.8.2
---

# files +upload

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Upload a file (auto small PUT or chunked upload session for >4 MB)

Run `mgs files +upload --help` for the live flag list.

## Usage

```bash
mgs files +upload <LOCAL> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `local` | ✓ | — | Local file to upload |
| `--to` | — | — | Remote folder or path (default: drive root) |
| `--name` | — | — | Rename on upload |
| `--chunk-mb` | — | 10 | Chunk size for large uploads |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs files +upload ./report.pdf --to /Documents
mgs files +upload ./big.zip --chunk-mb 10
```

## Tips

- Files over 4 MB upload via a chunked session automatically.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-files](../mgs-files/SKILL.md) — All files commands
