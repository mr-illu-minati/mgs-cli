# App-only auth (managed identity / workload federation / secret) — design

**Date:** 2026-07-31
**Status:** Approved for planning

## Problem

Today `mgs` authenticates only as a signed-in user: MSAL delegated public-client flows
(browser / device-code / silent) plus a raw `MGS_TOKEN` escape hatch. There is no way for
`mgs` to run **unattended** — as a daemon, in CI, or inside an Azure-hosted workload — where
the CLI must authenticate as *itself* (application permissions) rather than as a person.

We want an **app-only** track covering the three unattended mechanisms:

1. **Client secret / certificate** — a service principal with a stored credential.
2. **Workload identity federation** — an OIDC federated credential (no stored secret), e.g.
   GitHub Actions or AKS.
3. **Managed identity** — the ambient identity of an Azure host (VM, Container App,
   Functions, AKS).

## Non-goals

- No `azure-identity` / `DefaultAzureCredential` dependency (see "Library choice").
- No `az` / Azure PowerShell / Developer-CLI credential passthrough — those are developer
  conveniences, not unattended server auth.
- No change to the delegated track's behavior, scopes, or performance.
- `MGS_SCOPES` remains **delegated-only** and does not apply to app-only.

## Library choice: `msal`-native, no new dependency

`msal` (already a dependency) covers all three mechanisms, so we do **not** add
`azure-identity`:

| Mechanism | `msal` API |
|---|---|
| Secret / cert | `ConfidentialClientApplication.acquire_token_for_client(["…/.default"])` |
| Workload federation | read `AZURE_FEDERATED_TOKEN_FILE`, pass its contents as `client_assertion` to `ConfidentialClientApplication` |
| Managed identity | `msal.ManagedIdentityClient(...).acquire_token_for_client(resource=…)` (handles IMDS / App Service / Arc endpoints) |

We write only the small ordering/selection logic and the federated-token-file read. This keeps
the base install tiny and the interactive fast path unchanged. `msal` is imported lazily (as
today) — never loaded on the valid-cache fast path.

## Token model

App-only requests the **`https://graph.microsoft.com/.default`** scope and receives a token
carrying the **application** Graph permissions that an admin has consented to on the app in
Entra ID (e.g. `Mail.Read`, `User.Read.All`). This is distinct from the delegated track's
incremental user scopes. `MGS_SCOPES` does not affect app-only.

Managed identity uses the Graph **resource** form (`https://graph.microsoft.com`) rather than
the `/.default` scope string, per `ManagedIdentityClient`'s API; the effect is the same.

## Control surface: `MGS_AUTH`

A single environment variable selects the track and can pin a specific mechanism
(short-circuiting the chain):

| `MGS_AUTH` value | Behavior |
|---|---|
| *(unset)* / `delegated` | Delegated track (browser / device / silent). **Default.** |
| `app-only` | Full app-only chain, in order: secret → workload federation → managed identity. |
| `secret` | Pin client-secret/cert only. |
| `workload` | Pin workload identity federation only. |
| `managed-identity` (alias `msi`) | Pin managed identity only. |

- An **unknown** `MGS_AUTH` value is a `UsageError` that lists the valid values.
- **Explicit always wins.** Pinning a mechanism that has no usable credential is a clear
  `AuthError` naming the missing input (e.g. "MGS_AUTH=secret but no client secret found").

### Ambient auto-detection (only when `MGS_AUTH` is unset)

To make Azure-hosted / CI runs work with zero config, when `MGS_AUTH` is **unset** the
app-only track engages automatically if app-only credentials are detectably present:

- a client secret is set (`AZURE_CLIENT_SECRET` or `MGS_CLIENT_SECRET`), **or**
- a federated token file is set (`AZURE_FEDERATED_TOKEN_FILE`), **or**
- an ambient managed identity endpoint is available.

Otherwise the delegated track runs (unchanged). Because auto-detection only applies with
`MGS_AUTH` unset, explicit configuration is never surprising.

## Configuration inputs

Standard `AZURE_*` names are read natively (what CI and Azure already inject), with `MGS_*`
aliases for consistency with existing config:

| Purpose | Primary | Alias |
|---|---|---|
| Client id | `AZURE_CLIENT_ID` | `MGS_CLIENT_ID` |
| Tenant id | `AZURE_TENANT_ID` | `MGS_TENANT_ID` |
| Client secret | `AZURE_CLIENT_SECRET` | `MGS_CLIENT_SECRET` |
| Certificate (path or PEM + thumbprint) | `AZURE_CLIENT_CERTIFICATE_PATH` | `MGS_CLIENT_CERTIFICATE_PATH` |
| Federated token file | `AZURE_FEDERATED_TOKEN_FILE` | — |
| User-assigned MI client id | `AZURE_CLIENT_ID` | `MGS_CLIENT_ID` |

App-only requires a real tenant (not `common`); if tenant is unset/`common` in an app-only
context, error clearly.

## Resolution order (overall)

```
MGS_TOKEN (raw)                → return as-is
valid fast-path cache          → return (no msal import, no network)
track = delegated (default) unless MGS_AUTH selects app-only,
        or MGS_AUTH unset AND ambient app-only creds detected
  app-only  → msal app-only chain (or pinned mechanism)  → .default token
  delegated → msal silent → browser / device             → incremental token
write fast-path cache (0600); return access_token
```

The fast-path cache (`token.json`) and `MGS_TOKEN` sit **above both tracks**: once either
mints a token, later commands hit the same ~33 ms cached path. App-only skips the MSAL *user*
cache (`msal_cache.json`) — app-only tokens are cheap to re-mint from the credential — but
still writes the fast-path cache so back-to-back invocations don't re-hit the token endpoint.

## Components / changes

- **`config.py`**
  - `resolve_auth_mode() -> str` — normalizes `MGS_AUTH` to one of
    `delegated | app-only | secret | workload | managed-identity`; raises `UsageError` on an
    unknown value. When unset, returns `delegated` unless ambient app-only creds are detected.
  - `resolve_client_secret()`, `resolve_cert()`, `resolve_federated_token_file()` — read the
    `AZURE_*` / `MGS_*` inputs above.
  - Small `_ambient_app_only() -> bool` helper for auto-detection.
- **`auth.py`**
  - `_acquire_app_only(config_dir, mode) -> str` — new function implementing the chain and the
    pinned-mechanism short-circuits via `ConfidentialClientApplication` /
    `ManagedIdentityClient`. Reads the federated token file for `workload`.
  - `get_token()` branches on `resolve_auth_mode()`: app-only modes → `_acquire_app_only`;
    delegated → existing `_acquire_via_msal`.
  - `login()` under an app-only mode performs a non-interactive credential check (acquire a
    token and report success) rather than opening a browser.
- **Errors** reuse `AuthError` (with actionable, mechanism-specific detail) and `UsageError`.

## Error handling

- Unknown `MGS_AUTH` → `UsageError` listing valid values.
- Pinned mechanism with no usable credential → `AuthError` naming the missing input.
- App-only chain exhausted → `AuthError` summarizing what each leg tried and why it was
  skipped/failed.
- App-only with tenant `common`/unset → `AuthError` telling the user to set a real tenant.
- Graph 403 on an app-only token → surfaced by the existing Graph error path, hinting that the
  app is missing an **application** permission / admin consent (distinct from delegated scope).

## Testing

Unit tests, no network (mock `msal` clients and env):

- `resolve_auth_mode`: unset→delegated; each explicit value; unknown→`UsageError`; ambient
  detection flips unset→app-only only when creds present.
- Config readers: `AZURE_*` primary, `MGS_*` alias, precedence.
- `_acquire_app_only`: secret path builds `ConfidentialClientApplication` and calls
  `acquire_token_for_client`; workload path reads the token file and passes a `client_assertion`;
  managed-identity path uses `ManagedIdentityClient`; each pinned mode skips the others; missing
  credential → `AuthError`.
- `get_token` routes to the app-only path under app-only modes and still honors `MGS_TOKEN` and
  the fast-path cache above the branch.
- Regression: delegated path and existing tests unchanged (150 passing today).

## Docs

- `docs/auth-production.md`: new "App-only auth" section (the `MGS_AUTH` table, the three
  mechanisms, application-vs-delegated permissions, admin consent, env var table).
- `README.md`: brief app-only note + env table rows for `MGS_AUTH` / `AZURE_CLIENT_SECRET` /
  `AZURE_FEDERATED_TOKEN_FILE`.
- Skills `SHARED_MD` env list: add `MGS_AUTH`.

## Rollout

Additive and backward-compatible: with `MGS_AUTH` unset and no ambient app-only creds, behavior
is identical to today. Version bump on ship.
