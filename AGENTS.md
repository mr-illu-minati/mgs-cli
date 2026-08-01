# mgs — Microsoft 365 CLI for AI agents

`mgs` drives Microsoft 365 (Outlook mail & calendar, OneDrive/SharePoint files, Teams,
Excel, OneNote) via Microsoft Graph. This guide is agent-agnostic — it works with any
assistant that reads `AGENTS.md` (Codex, Cursor, Gemini CLI, Amp, Claude Code, …).
Per-command references live in `skills/<name>/SKILL.md`; the index is `skills/SKILLS.md`.

## Setup

- Needs the `mgs` command on PATH (see the project README) and a one-time `mgs auth login`.
- Check auth with `mgs auth status`. Headless/CI: `MGS_NO_BROWSER=1 mgs auth login`.

## Command model

```
mgs <service> <verb> [flags]
```

- Verbs: `list`, `get <id>`, `create --json '{…}'`, `update <id> --json '{…}'`,
  `delete <id>`, any bound action (see `mgs schema <service>`), or a `+helper`.
- Output is JSON on stdout; errors are JSON on stderr with a non-zero exit code.
- Preview writes first: append `--dry-run` to any command to see the exact request
  that would be sent, without sending it.

## Discover commands

```bash
mgs --help                 # list services
mgs <service> --help       # verbs + helpers for a service
mgs schema <service>       # properties, navigations, bound actions
```

## Services and helpers

### mail — Read, send, and manage Outlook mail
- `mgs mail +send` — Send an email (--to/--cc/--bcc --subject --body [--html] [--attach] [--draft])
- `mgs mail +read` — Read a message and render clean body/headers
- `mgs mail +reply` — Reply to a message (threading handled by Graph)
- `mgs mail +reply-all` — Reply-all to a message
- `mgs mail +forward` — Forward a message to new recipients
- `mgs mail +triage` — Summarize unread mail (ranked, compact) for fast scanning
- `mgs mail +watch` — Stream new mail as NDJSON via Graph delta polling

### calendar — Manage Outlook calendar events
- `mgs calendar +agenda` — Show upcoming events (calendarView; expands recurrences)
- `mgs calendar +insert` — Create a calendar event (conflict-checked unless --no-conflict-check)

### files — Browse and manage OneDrive/SharePoint files
- `mgs files +upload` — Upload a file (auto small PUT or chunked upload session for >4 MB)
- `mgs files +download` — Download a drive item (by id or /path) to a local file

### users — Look up users in the directory
- generic verbs only (`mgs users list/get/create/update/delete`)

### teams — Microsoft Teams: teams, channels, messages
- `mgs teams +send` — Send a Teams message to a channel (--team/--channel) or chat (--chat)
- `mgs teams +channels` — List channels in a team
- `mgs teams +chats` — List your recent chats (for discovering chat ids)

### excel — Excel workbooks (helpers: +read/+append)
- `mgs excel +read` — Read an Excel worksheet range or usedRange
- `mgs excel +append` — Append a row to an Excel table

### onenote — OneNote pages
- `mgs onenote +write` — Create a OneNote page (--title, --content, [--html], [--section])

## Global flags

`--dry-run` · `--beta` · `--page-all` · `--json '{…}'` · `--params '{…}'` ·
OData `--select` / `--filter` / `--orderby` / `--expand` / `--search` / `--top` / `--skip`.

## Safety rules for agents

- Confirm with the user before any write/delete command; prefer `--dry-run` first.
- Never echo tokens or secrets.
- Writes (`+send`, `+reply`, `+insert`, `delete`, bound actions) are real and immediate.
