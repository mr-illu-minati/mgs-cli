# mgs — One CLI for Microsoft 365

`mgs` is a fast Python CLI for Microsoft 365 — built for humans **and AI agents**. It builds
its command surface dynamically from Microsoft Graph's CSDL metadata and covers Outlook mail &
calendar, OneDrive/SharePoint files, Teams, Excel, OneNote, and directory users. It is the
Microsoft counterpart to the `gws` Google Workspace CLI.

- Structured JSON output on every command
- `--dry-run` on every write; OData `--select/--filter/--top/...`; `--page-all`
- Zero-setup browser login (Entra ID via MSAL); `mgs schema <service>` introspection
- ~33 ms local overhead; one runtime dependency (`msal`)
- Generated agent skills (`SKILL.md` + `AGENTS.md`) so any agent can drive it

## Install

Requires **Python 3.10+**. The package is **`mgs-cli`**; the command it installs is **`mgs`**.
Easiest via [`uv`](https://docs.astral.sh/uv/) or `pipx`:

```bash
uv tool install mgs-cli        # or: pipx install mgs-cli   → provides the `mgs` command
```

Run without installing: `uvx --from mgs-cli mgs --help`.

**From source:**

```bash
git clone https://github.com/mr-illu-minati/mgs-cli && cd mgs-cli
uv tool install .                       # installs the `mgs` command globally
# or, for development:
uv sync && uv run mgs --help            # and: uv run pytest
```

Update with `uv tool upgrade mgs-cli`, remove with `uv tool uninstall mgs-cli`.

## Quick start

```bash
mgs auth login                                   # browser sign-in (Entra ID)
mgs mail +triage --max 5
mgs calendar +agenda --week --timezone America/Toronto
mgs files +upload ./report.pdf --to /Documents
mgs mail +send --to you@example.com --subject Hi --body "It works"
mgs schema mail                                  # introspect a service
```

> Login works out of the box: `mgs` ships its own registered multi-tenant Entra app
> ("mgs CLI"), so `mgs auth login` needs no setup. Organizations can bring their own app via
> `MGS_CLIENT_ID`. For unattended/server/CI use, set `MGS_AUTH` for **app-only** auth (client
> secret, workload identity federation, or managed identity). Details, scopes, and admin
> consent: [docs/auth-production.md](docs/auth-production.md).

## Commands

```
mail      list get create update delete  +send +read +reply +reply-all +forward +triage +watch
calendar  list get create update delete  +agenda +insert
files     list get create update delete  +upload +download
teams     list get create update delete  +send +channels +chats
excel     list get create update delete  +read +append
onenote   list get create update delete  +write
users     list get create update delete
auth login|logout|status   ·   schema <service>   ·   skills install   ·   generate-skills
```

Every service also accepts **bound actions** (e.g. `mgs mail move <id> --json '{...}'`) and
raw bodies via `--json` / `--params`. Discover anything with `mgs <service> --help` and
`mgs schema <service>`.

## Using mgs with AI agents (any platform)

`mgs` ships a generated, **agent-agnostic** skill set — no platform lock-in.

### Install skills into a project

```bash
mgs skills install --dir /path/to/repo   # default targets: claude + agents
mgs skills install --target all          # claude + agents
mgs skills install --target cursor       # Cursor only
mgs skills install --global              # write to global skill dirs (~/.claude/skills etc.)
mgs skills install --prune               # also remove stale mgs-* skills from a previous version
```

The command is **idempotent** — re-running it when nothing changed reports `added: 0`.
It never touches skill directories that don't start with `mgs-`.

### Target directories

| `--target` | project dir | global dir | loaded by |
|---|---|---|---|
| `claude` (default) | `.claude/skills` | `~/.claude/skills` | Claude Code, GitHub Copilot, OpenCode |
| `agents` (default) | `.agents/skills` | `~/.agents/skills` | Cursor, OpenCode |
| `cursor` | `.cursor/skills` | `~/.cursor/skills` | Cursor |
| `opencode` | `.opencode/skills` | `~/.config/opencode/skills` | OpenCode |

### AGENTS.md

`AGENTS.md` at the **repo root** is the single agent-agnostic entry point read automatically by
Codex, Cursor, Gemini CLI, Amp, Claude Code, and others. Generate or update it with:

```bash
mgs generate-skills --out skills   # writes skills/AGENTS.md; copy or symlink to repo root
```

The committed `AGENTS.md` at the root of this repo is kept up to date.

### Low-level primitive

```bash
mgs generate-skills --out skills   # writes skills/<name>/SKILL.md + SKILLS.md + AGENTS.md
```

The recipient needs `mgs` installed and `mgs auth login` done once.

## Performance

The 2.7 MB Graph `$metadata` is parsed at most once per 24 h and cached as compact
per-EntityType JSON, so a typical command loads a few-KB file. MSAL is imported only when a
token must be acquired or refreshed; a valid cached token skips it entirely.

## Environment variables

| Variable | Purpose |
|---|---|
| `MGS_TOKEN` | Pre-obtained Graph access token (highest priority) |
| `MGS_CLIENT_ID` / `MGS_TENANT_ID` | Bring-your-own Entra app + tenant (default tenant: `common`) |
| `MGS_SCOPES` | Delegated Graph scopes to request at login (space/comma-separated; default: all). Handy with a minimal BYO app. |
| `MGS_CONFIG_DIR` | Config dir override (default `~/.config/mgs`) |
| `MGS_NO_BROWSER` | Use device-code login instead of the browser (headless/CI) |
| `MGS_AUTH` | Auth mode: `delegated` (default), `app-only`, `secret`, `workload`, `managed-identity` — for unattended/server/CI use ([details](docs/auth-production.md)) |
| `AZURE_CLIENT_SECRET` / `MGS_CLIENT_SECRET` | App-only client secret (service principal) |
| `AZURE_CLIENT_CERTIFICATE_PATH` | App-only certificate (PEM) |
| `AZURE_FEDERATED_TOKEN_FILE` | App-only workload identity federation (OIDC) token file |
| `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` | Standard fallbacks |

## License

MIT — see [LICENSE](LICENSE).
