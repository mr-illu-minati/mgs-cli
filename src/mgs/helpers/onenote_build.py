"""Pure builders for OneNote page creation (XHTML document, target path)."""

from __future__ import annotations

import html as htmllib

from mgs.validate import encode_path_segment, validate_resource_name


def build_page_html(title: str, content: str, is_html: bool) -> str:
    if is_html:
        body = content or ""
    else:
        escaped = htmllib.escape(content or "")
        body = "<p>" + escaped.replace("\n", "</p><p>") + "</p>"
    t = htmllib.escape(title or "")
    return f"<!DOCTYPE html><html><head><title>{t}</title></head><body>{body}</body></html>"


def pages_path(section: str | None) -> str:
    if section:
        validate_resource_name(section)
        return f"/me/onenote/sections/{encode_path_segment(section)}/pages"
    return "/me/onenote/pages"
