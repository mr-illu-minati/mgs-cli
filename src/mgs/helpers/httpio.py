"""Raw-bytes HTTP for uploads/downloads (stdlib urllib), separate from the JSON GraphClient."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from mgs.errors import HttpError

_TIMEOUT = 600


def put_bytes(url: str, data: bytes, headers: dict | None = None) -> object:
    req = urllib.request.Request(url, data=data, method="PUT", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            text = resp.read().decode(errors="replace")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise HttpError(detail or str(e.reason), status=e.code) from e
    except urllib.error.URLError as e:
        raise HttpError(str(e.reason), status=0) from e


def post_bytes(url: str, data: bytes, headers: dict | None = None) -> object:
    req = urllib.request.Request(url, data=data, method="POST", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            text = resp.read().decode(errors="replace")
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise HttpError(detail or str(e.reason), status=e.code) from e
    except urllib.error.URLError as e:
        raise HttpError(str(e.reason), status=0) from e


def get_to_file(url: str, dest: str, headers: dict | None = None) -> str:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp, open(dest, "wb") as f:
            while True:
                chunk = resp.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
    except urllib.error.HTTPError as e:
        raise HttpError(str(e.reason), status=e.code) from e
    except urllib.error.URLError as e:
        raise HttpError(str(e.reason), status=0) from e
    return dest
