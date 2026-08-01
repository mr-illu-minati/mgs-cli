"""Pure builders for mail helper payloads (recipients, message, attachments, HTML->text)."""

from __future__ import annotations

import base64
import html as htmllib
import os
import re

from mgs.errors import UsageError

MAX_ATTACH_BYTES = 25 * 1024 * 1024


def parse_recipients(raw: str | None) -> list[dict]:
    if not raw:
        return []
    out = []
    for part in raw.split(","):
        addr = part.strip()
        if addr:
            out.append({"emailAddress": {"address": addr}})
    return out


def file_attachment(path: str) -> dict:
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        raise UsageError(f"cannot read attachment {path!r}: {e}")
    if len(data) > MAX_ATTACH_BYTES:
        raise UsageError(f"attachment {path!r} exceeds 25 MB")
    return {
        "@odata.type": "#microsoft.graph.fileAttachment",
        "name": os.path.basename(path),
        "contentBytes": base64.b64encode(data).decode("ascii"),
    }


def build_message(
    subject: str,
    body: str,
    *,
    html: bool,
    to: str | None,
    cc: str | None,
    bcc: str | None,
    attach: list[str] | None,
) -> dict:
    to_r, cc_r, bcc_r = parse_recipients(to), parse_recipients(cc), parse_recipients(bcc)
    if not (to_r or cc_r or bcc_r):
        raise UsageError("at least one of --to/--cc/--bcc is required")
    msg: dict = {
        "subject": subject or "",
        "body": {"contentType": "HTML" if html else "Text", "content": body or ""},
    }
    if to_r:
        msg["toRecipients"] = to_r
    if cc_r:
        msg["ccRecipients"] = cc_r
    if bcc_r:
        msg["bccRecipients"] = bcc_r
    if attach:
        total = 0
        atts = []
        for p in attach:
            a = file_attachment(p)
            total += len(a["contentBytes"])
            atts.append(a)
        if total > MAX_ATTACH_BYTES:
            raise UsageError("total attachments exceed 25 MB")
        msg["attachments"] = atts
    return msg


_TAG = re.compile(r"<[^>]+>")
_BR = re.compile(r"(?i)<br\s*/?>|</p>|</div>")


def html_to_text(content: str) -> str:
    """Crude but dependency-free HTML -> text: line-break block tags, strip the rest, unescape."""
    if content is None:
        return ""
    text = _BR.sub("\n", content)
    text = _TAG.sub("", text)
    text = htmllib.unescape(text)
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)
