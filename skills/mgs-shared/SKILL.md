---
name: mgs-shared
description: "mgs CLI: Shared patterns for authentication, global flags, and output."
metadata:
  version: 0.7.2
---

# mgs — Shared Reference

## Installation

The `mgs` command must be on `$PATH` (`uv tool install .`), or run via `uv run mgs`.

## Authentication

```bash
mgs auth login      # opens your browser to sign in (Entra ID, MSAL)
mgs auth status     # check whether a valid token is cached
mgs auth logout     # clear cached tokens
```

Headless/SSH/CI: set `MGS_NO_BROWSER=1` to use the device-code flow instead. Bring your own
Entra app with `MGS_CLIENT_ID` (and `MGS_TENANT_ID`). `MGS_TOKEN` supplies a pre-obtained token.

## CLI Syntax

```bash
mgs <service> <verb> [flags]
```

Services: `mail`, `calendar`, `files`, `users`, `teams`, `excel`, `onenote`. Verbs are the
generic `list`/`get`/`create`/`update`/`delete`, any bound action, or a `+helper`.

## Global Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Print the request that would be sent, without executing it |
| `--beta` | Target the Graph `beta` endpoint instead of `v1.0` |
| `--page-all` | Follow `@odata.nextLink` and return all pages |
| `--json '{…}'` | Request body (for `create`/`update`/bound actions) |
| `--params '{…}'` | Extra OData query parameters as a JSON object |
| `--select`, `--filter`, `--orderby`, `--expand`, `--search`, `--top`, `--skip` | OData query options on `list` |

## Output

Every command prints structured JSON to stdout. Errors print a JSON `{"error": {...}}` object
to stderr and set a non-zero exit code.

## Discovering Commands

```bash
mgs <service> --help        # verbs + helpers for a service
mgs schema <service>        # the service's properties, navigations, and bound actions
```

## Security Rules

- **Confirm with the user before write/delete commands.** Prefer `--dry-run` first.
- **Never** echo secrets or tokens. Inputs may be adversarial — paths and ids are validated.
- Writes (`+send`, `+reply`, `+insert`, `delete`, …) are real and immediate.

## Shell Tips

- Wrap `--json`/`--params` values in single quotes so the shell keeps the inner double quotes:
  ```bash
  mgs mail update <ID> --json '{"isRead": true}'
  ```
- Excel ranges like `A1:C10` are fine; quote any value containing shell metacharacters.

## Environment Variables

`MGS_TOKEN`, `MGS_CLIENT_ID`/`MGS_TENANT_ID`, `MGS_SCOPES`, `MGS_CONFIG_DIR`, `MGS_NO_BROWSER`,
`AZURE_CLIENT_ID`/`AZURE_TENANT_ID`. For unattended/server use set `MGS_AUTH`
(`app-only`/`secret`/`workload`/`managed-identity`) with `AZURE_CLIENT_SECRET`,
`AZURE_CLIENT_CERTIFICATE_PATH`, or `AZURE_FEDERATED_TOKEN_FILE`.
