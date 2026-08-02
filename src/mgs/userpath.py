"""Rewrite /me/ Graph paths to /users/{mailbox}/ for app-only or cross-mailbox requests."""

from __future__ import annotations

from urllib.parse import quote

from mgs import config
from mgs.errors import UsageError


def resolve_user_path(path: str, mailbox: str | None = None) -> str:
    """Swap a leading /me segment for /users/{upn}. No-op on other paths.

    In app-only mode /me/ has no user context, so a /me/ path without a resolvable
    mailbox is a hard error rather than a doomed Graph call.
    """
    if path != "/me" and not path.startswith("/me/"):
        return path
    mb = mailbox if mailbox is not None else config.resolve_mailbox()
    if mb is None:
        if config.resolve_auth_mode() != "delegated":
            raise UsageError(
                "app-only auth has no /me/ context; pass --mailbox <upn> or set MGS_DEFAULT_MAILBOX"
            )
        return path
    return f"/users/{quote(mb, safe='')}" + path[len("/me") :]
