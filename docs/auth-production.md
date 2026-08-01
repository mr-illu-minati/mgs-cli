# mgs authentication

How `mgs` signs in to Microsoft Graph, the app it uses, and how to bring your own.

## How auth works

`mgs` is a **public client** — a distributed CLI that cannot keep a secret. It uses Microsoft's
**MSAL** library to obtain **delegated** Microsoft Graph access tokens (the CLI acts as *you*):

- `mgs auth login` → `acquire_token_interactive()` (opens the browser) by default, or
  `acquire_token_by_device_flow()` when `MGS_NO_BROWSER=1` (headless/SSH/CI).
- Subsequent commands reuse a cached token via a fast path (no MSAL import, no network) and
  silently refresh through the MSAL token cache when the access token expires.
- `MGS_TOKEN` supplies a pre-obtained access token and bypasses login entirely.

For unattended/server/CI use, `mgs` also supports **app-only** auth (the CLI acts as *itself*
with application permissions) via `MGS_AUTH` — see [App-only auth](#app-only-auth-unattended--server--ci) below.

Every public client needs a **client id**. (MSAL has no implicit default, and
`azure-identity`'s `InteractiveBrowserCredential` default app is scoped for Azure Resource
Manager, not Graph — so it can't serve `mgs`.)

## The built-in app: "mgs CLI"

`mgs` ships with its own registered Entra application so login works with **zero setup**:

| | |
|---|---|
| Name (shown on consent) | **mgs CLI** |
| Client id (`config.BUILTIN_CLIENT_ID`) | `59b3a13e-fefb-4ded-872f-143ea9bfce27` |
| Type | Public client (no secret), loopback redirect `http://localhost` |
| Audience | Multi-tenant (any Entra ID organization) |
| Permissions | Delegated Microsoft Graph — see `auth.SCOPES` |

Because it's a real registration owned by the project, tenant sign-in logs show **"mgs CLI"**
(honest and auditable), and Microsoft won't revoke it out from under us the way a borrowed
first-party id could.

**Requested scopes** (`src/mgs/auth.py`): `User.Read`, `User.ReadBasic.All`, `Mail.ReadWrite`,
`Mail.Send`, `Calendars.ReadWrite`, `Files.ReadWrite.All`, `Team.ReadBasic.All`,
`Channel.ReadBasic.All`, `ChannelMessage.Send`, `Chat.ReadWrite`, `Notes.ReadWrite`. MSAL
requests these incrementally at login; the user (or a tenant admin) consents.

## Enterprise admin consent

Many tenants disable user consent to third-party apps. In those tenants a **tenant admin must
approve `mgs` once** before regular users can sign in — Microsoft tenant policy, not something
`mgs` controls. An admin grants it with:

```
https://login.microsoftonline.com/{tenant}/adminconsent?client_id=59b3a13e-fefb-4ded-872f-143ea9bfce27
```

(Replace `{tenant}` with the tenant id or domain, or use `common`.) After that, every user in
that tenant can `mgs auth login` without their own consent prompt.

## Bring your own app (recommended for organizations)

Security-conscious orgs can run `mgs` under **their own** Entra app instead of the shipped one
— full control over consent, scopes, branding, and audit:

```bash
export MGS_CLIENT_ID=<your-app-client-id>
export MGS_TENANT_ID=<your-tenant-id-or-domain>   # optional; default: common
```

`AZURE_CLIENT_ID` / `AZURE_TENANT_ID` are honored as fallbacks. Register the app as a
**public client** with `http://localhost` as a redirect URI, enable "Allow public client
flows", and add the delegated Graph permissions listed above.

**Minimal-scope apps.** `mgs` requests all of the scopes above at login by default, so a
narrowly-scoped app (e.g. mail-only) can hit an admin-consent prompt for scopes it does not
have. Set `MGS_SCOPES` to request only what your app supports:

```bash
export MGS_SCOPES="User.Read Mail.ReadWrite Mail.Send"
mgs auth logout && mgs auth login
```

Commands that need a scope you did not request return a clear permission error.

## Tenant selection

`MGS_TENANT_ID` chooses the authority: `common` (default — any work/school or personal
account), `organizations` (work/school only), `consumers` (personal only), or a specific
tenant id/domain to pin sign-in to one organization.

## App-only auth (unattended / server / CI)

Beyond the interactive delegated flows above, `mgs` can authenticate **as itself** with
Microsoft Graph **application** permissions — for daemons, cron jobs, CI, and Azure-hosted
workloads. Set `MGS_AUTH` to choose the track and, optionally, pin one mechanism:

| `MGS_AUTH` | Behavior |
|---|---|
| *(unset)* / `delegated` | Interactive delegated login (browser/device). **Default.** |
| `app-only` | Try, in order: client secret/cert → workload identity federation → managed identity. |
| `secret` | Pin client secret or certificate only. |
| `workload` | Pin workload identity federation (OIDC) only. |
| `managed-identity` (alias `msi`) | Pin the Azure host's managed identity only. |

### Auto-detection when `MGS_AUTH` is unset

When `MGS_AUTH` is **unset**, `mgs` auto-selects `app-only` only if it detects an actual
unattended **credential** in the environment:

- a client secret (`AZURE_CLIENT_SECRET` / `MGS_CLIENT_SECRET`), **or**
- a federated token file (`AZURE_FEDERATED_TOKEN_FILE`), **or**
- a managed-identity **endpoint** env var (`IDENTITY_ENDPOINT` or `MSI_ENDPOINT`).

Otherwise it uses the delegated (browser) flow. Explicit `MGS_AUTH` always wins.

> **A bare client id is not a credential.** Setting only `AZURE_CLIENT_ID` (or `MGS_CLIENT_ID`)
> does **not** trigger app-only — it just says *which app* to use for the normal interactive
> login. App-only engages only when one of the credentials above is present, or when you set
> `MGS_AUTH` explicitly.

**Plain Azure VMs need an explicit `MGS_AUTH=managed-identity`.** PaaS hosts (App Service,
Functions, Container Apps, Arc, Service Fabric, Cloud Shell) inject `IDENTITY_ENDPOINT`, so
`mgs` auto-detects them. A raw IaaS VM exposes its managed identity only through the IMDS
endpoint (`169.254.169.254`) with **no env var**, so auto-detection can't see it — set
`MGS_AUTH=managed-identity` there. (`mgs` deliberately never probes IMDS during detection: that
would add a network call, and a hang off Azure, to the fast interactive path.)

**`MGS_*` beats `AZURE_*` — avoid conflicting values.** For every pair below, if both are set to
*different* values, the `MGS_*` one silently wins. In CI / Azure-hosted contexts (which inject
`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_FEDERATED_TOKEN_FILE`), a leftover `MGS_CLIENT_ID`
from an interactive setup will override the injected app id and break auth confusingly. Set only
one per pair — prefer the standard `AZURE_*` names in unattended/CI environments.

**App-only uses application permissions, not delegated scopes.** Grant the app the Graph
**application** permissions it needs (e.g. `Mail.Read`, `User.Read.All`) and have an admin
consent to them once in Entra ID. `MGS_SCOPES` applies only to the delegated flow and is
ignored here. App-only also requires a **specific tenant** — set `MGS_TENANT_ID` /
`AZURE_TENANT_ID` (not `common`).

Credentials are read from standard `AZURE_*` variables (with `MGS_*` aliases):

| Purpose | Primary | Alias |
|---|---|---|
| Client id | `AZURE_CLIENT_ID` | `MGS_CLIENT_ID` |
| Tenant id | `AZURE_TENANT_ID` | `MGS_TENANT_ID` |
| Client secret | `AZURE_CLIENT_SECRET` | `MGS_CLIENT_SECRET` |
| Certificate (PEM path) | `AZURE_CLIENT_CERTIFICATE_PATH` | `MGS_CLIENT_CERTIFICATE_PATH` |
| Federated token file (OIDC) | `AZURE_FEDERATED_TOKEN_FILE` | — |
| User-assigned MI client id | `AZURE_CLIENT_ID` | `MGS_CLIENT_ID` |

```bash
# Service principal with a secret
export MGS_AUTH=secret
export AZURE_TENANT_ID=contoso.onmicrosoft.com
export AZURE_CLIENT_ID=<app-id>
export AZURE_CLIENT_SECRET=<secret>
mgs users +me

# Azure VM / Container App with a managed identity
export MGS_AUTH=managed-identity
mgs mail +read

# GitHub Actions via workload identity federation (OIDC)
export MGS_AUTH=workload
# AZURE_CLIENT_ID / AZURE_TENANT_ID / AZURE_FEDERATED_TOKEN_FILE injected by the OIDC step
mgs users +me
```

No `azure-identity` dependency is required — `mgs` implements these flows directly on MSAL.

## Token storage

MSAL's serialized token cache and a fast-path `token.json` are written to
`~/.config/mgs/` (override with `MGS_CONFIG_DIR`) with `0600` permissions. At-rest encryption
via the OS keychain (`msal-extensions`) is a planned hardening step.

## Roadmap

- **Publisher verification** for the "mgs CLI" app — removes the "unverified app" consent
  banner and raises consent limits. Requires a Microsoft Partner account.
- **OS-keychain-backed** encrypted token cache.
