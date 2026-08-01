---
name: mgs-onenote-write
description: "OneNote: Create a OneNote page (--title, --content, [--html], [--section])"
metadata:
  version: 0.7.2
---

# onenote +write

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Create a OneNote page (--title, --content, [--html], [--section])

Run `mgs onenote +write --help` for the live flag list.

## Usage

```bash
mgs onenote +write --title <TITLE> [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--title` | ✓ | — | Page title |
| `--content` | — | — | Page content (HTML or plain text) |
| `--html` | — | — | Treat --content as HTML fragment |
| `--section` | — | — | Target section id (default: default notebook) |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs onenote +write --title 'Notes' --content 'Hello'
mgs onenote +write --title 'Doc' --content '<p>HTML</p>' --html --section <SECTION_ID>
```

## Tips

- Plain --content is escaped and wrapped in <p>; use --html to pass a fragment.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-onenote](../mgs-onenote/SKILL.md) — All onenote commands
