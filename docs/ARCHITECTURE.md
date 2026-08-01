# mgs — Architecture

`mgs` is a fast Python CLI for Microsoft 365, built for humans and AI agents. It is the
Microsoft counterpart to the `gws` Google Workspace CLI, adapted to how Microsoft exposes its
APIs.

## The core idea

`mgs` does not hard-code a static list of commands. It reads **Microsoft Graph's CSDL
`$metadata`** at runtime and builds its command surface from it, the way `gws` reads Google's
Discovery documents. The important difference from Google shapes everything:

| | Google (`gws`) | Microsoft (`mgs`) |
|---|---|---|
| API surface | Many per-service REST APIs | One unified API: **Microsoft Graph** |
| Machine description | Per-service Discovery JSON | One large **CSDL `$metadata`** (EDMX XML) |
| URL style | REST | **OData** (`$select`/`$filter`/`$top`/`@odata.nextLink`) |
| Auth | Google OAuth / GCP project | **Entra ID** via MSAL (delegated) |

### Two-phase dispatch

1. Read `argv[1]` (e.g. `mail`, `calendar`, `files`, `users`, `teams`, `excel`, `onenote`).
2. Resolve it via a **service registry** (`services.py`) to a Graph root path + root
   EntityType (e.g. `mail` → `/me/messages`, type `message`).
3. Load that EntityType from the **compact metadata cache** (see Performance).
4. Build only that service's `argparse` subparser, re-parse the remaining args.
5. Authenticate (fast-path token, else MSAL), build the OData request, execute, print JSON.

## Why Python (the speed bet)

The reference `gws` is Rust, and an early Rust prototype of the `mgs` engine was built first. We pivoted to Python because Microsoft's **MSAL** library
makes browser login a one-liner (`acquire_token_interactive()`), whereas Rust has no
`InteractiveBrowserCredential` and would need ~120 lines of hand-rolled OAuth.

The catch was **speed** — `mgs` must feel instant, including under agents firing many calls.
Python's interpreter startup and naive 2.7 MB XML re-parsing would undercut that, so the design
counters it deliberately (below). The bet paid off: steady-state local overhead is ~33 ms.

## Performance strategy

Every choice below exists to keep per-invocation overhead well under ~100 ms:

- **Stdlib-first, lazy heavy imports.** The CLI is `argparse`; HTTP is `urllib`; XML is
  `xml.etree`. The only third-party runtime dependency is **`msal`**, imported *only* when a
  token must be acquired or refreshed. `--help`, `--dry-run`, and `schema` import nothing heavy.
- **Compact, pre-parsed metadata cache.** The 2.7 MB `$metadata` is parsed at most once per
  24 h (streaming `iterparse`) and written as **small per-EntityType JSON files**. A normal
  command loads a few-KB file, not megabytes of XML.
- **Fast-path token cache.** A tiny `token.json` lets an authenticated command with a valid
  token proceed with no MSAL import and no network. MSAL is touched only for login/refresh.

## Package layout (`src/mgs/`)

```
cli.py          two-phase dispatch entrypoint
errors.py       MgsError hierarchy (exit codes + JSON)
validate.py     path-segment encoding + resource-name validation
metadata.py     CSDL data model (dataclasses)
csdl.py         EDMX parse + compact per-EntityType cache
services.py     alias -> Graph path + EntityType registry
odata.py        OData query-option builder + nextLink
client.py       Graph HTTP client (retry, 429/Retry-After, paging)
config.py       config dir + MGS_/AZURE_ env resolution
auth.py         fast-path token cache + lazy MSAL (interactive/device/silent)
auth_commands.py  mgs auth login/logout/status
commands.py     build argparse subparser (generic verbs + helpers) from a service
executor.py     request-plan builder (dry-run) + executor
schema.py       mgs schema introspection
drivepath.py    OneDrive/SharePoint drive-item addressing
skills.py       generate/install mgs-* agent skills
helpers/        +verb helpers per area (mail, calendar, files, teams, excel, onenote) + shared builders
```

## Command model

Every service supports the **generic verbs** `list` / `get` / `create` / `update` / `delete`
(with `--json` bodies and OData flags), plus any **bound action** from the metadata
(`mgs mail move <id> --json …`), plus curated **`+verb` helpers** that do orchestration the
generic verbs can't — MIME/attachment handling, HTML↔text, chunked upload sessions, conflict
checks, delta polling. Every write supports `--dry-run`. All output is JSON.

The helper set mirrors `gws`'s productivity surface: mail (`+send/+read/+reply/+reply-all/
+forward/+triage/+watch`), calendar (`+agenda/+insert`), files (`+upload/+download`), teams
(`+send/+channels/+chats`), excel (`+read/+append`), onenote (`+write`).

## Authentication

`mgs` is a public client using **delegated** Graph permissions (it acts as the signed-in user).
It ships a registered multi-tenant Entra app ("mgs CLI") as the default client id so login works
with zero setup; `MGS_CLIENT_ID` brings your own app. Full details, scopes, admin-consent, and
tenant selection are in [auth-production.md](auth-production.md).

## Skills for agents

`mgs generate-skills` / `mgs skills install` emit portable `SKILL.md` files (the Agent Skills
standard) from the CLI's own registry + argparse metadata, so any agent — Claude Code, GitHub
Copilot, Cursor, OpenCode — can drive `mgs` without custom tooling. See the README.

## Testing

Pure logic (metadata parsing, OData building, payload builders, request planning, dry-run
output, skill generation) is unit-tested offline; live Graph calls are integration-only. The
suite runs in well under a second.
