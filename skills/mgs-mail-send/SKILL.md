---
name: mgs-mail-send
description: "Mail: Send an email (--to/--cc/--bcc --subject --body [--html] [--attach] [--from] [--header] [--draft])"
metadata:
  version: 0.8.2
---

# mail +send

> **PREREQUISITE:** Read `../mgs-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `mgs generate-skills` to create it.

Send an email (--to/--cc/--bcc --subject --body [--html] [--attach] [--from] [--header] [--draft])

Run `mgs mail +send --help` for the live flag list.

## Usage

```bash
mgs mail +send [flags]
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--to` | — | — | Recipient(s), comma-separated |
| `--cc` | — | — | CC recipient(s), comma-separated |
| `--bcc` | — | — | BCC recipient(s), comma-separated |
| `--subject` | — | — | Email subject |
| `--body` | — | — | Email body |
| `--html` | — | — | Treat body as HTML |
| `--attach` | — | — | File to attach (repeatable) |
| `--from` | — | — | Send-as address (e.g. a mailbox alias; requires SendFromAliasEnabled for aliases, or Send As rights for another mailbox) |
| `--header` | — | — | Custom header 'X-Name: value' (repeatable; Graph requires the X- prefix) |
| `--draft` | — | — | Save as draft instead of sending |
| `--dry-run` | — | — |  |
| `--beta` | — | — |  |

## Examples

```bash
mgs mail +send --to alice@example.com --subject 'Hi' --body 'Hello!'
mgs mail +send --to a@x.com --cc b@x.com --subject Report --body 'See attached' --attach report.pdf
mgs mail +send --to a@x.com --subject 'Bold' --body '<b>hi</b>' --html
mgs mail +send --to a@x.com --subject Draft --body 'wip' --draft
mgs mail +send --to a@x.com --subject Hi --body Yo --from alias@example.com --header 'X-Run-Id: 42'
```

## Tips

- Total attachments must stay under 25 MB.
- Use --draft to save to Drafts instead of sending.
- --from sends as a mailbox alias (needs SendFromAliasEnabled) or another mailbox (needs Send As rights).
- --header adds a custom internet header; Graph requires the X- name prefix.

## See Also

- [mgs-shared](../mgs-shared/SKILL.md) — Global flags and auth
- [mgs-mail](../mgs-mail/SKILL.md) — All mail commands
