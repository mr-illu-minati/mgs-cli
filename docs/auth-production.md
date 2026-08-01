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

## Token storage

MSAL's serialized token cache and a fast-path `token.json` are written to
`~/.config/mgs/` (override with `MGS_CONFIG_DIR`) with `0600` permissions. At-rest encryption
via the OS keychain (`msal-extensions`) is a planned hardening step.

## Roadmap

- **Publisher verification** for the "mgs CLI" app — removes the "unverified app" consent
  banner and raises consent limits. Requires a Microsoft Partner account.
- **App-only (client-credentials) flow** for unattended/server use, where the customer
  registers their own app with a secret or certificate and application Graph permissions.
- **OS-keychain-backed** encrypted token cache.
