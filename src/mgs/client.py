"""Microsoft Graph HTTP client over stdlib urllib, with retry/throttling and paging."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from mgs.errors import HttpError
from mgs.odata import NEXT_LINK

V1_BASE = "https://graph.microsoft.com/v1.0"
BETA_BASE = "https://graph.microsoft.com/beta"
MAX_RETRIES = 3
RETRY_AFTER_CAP = 120


def should_retry(status: int) -> bool:
    return status == 429 or 500 <= status <= 599


class GraphClient:
    def __init__(self, token: str, beta: bool = False) -> None:
        self.token = token
        self.base = BETA_BASE if beta else V1_BASE

    def full_url(self, path: str, query: str = "") -> str:
        return f"{self.base}{path}{query}"

    def request(
        self, method: str, url: str, body: dict | None = None, headers: dict | None = None
    ) -> object:
        data = json.dumps(body).encode() if body is not None else None
        hdrs = {"Authorization": f"Bearer {self.token}"}
        if data is not None:
            hdrs["Content-Type"] = "application/json"
        if headers:
            hdrs.update(headers)
        attempt = 0
        while True:
            req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
            try:
                with urllib.request.urlopen(req, timeout=100) as resp:
                    text = resp.read().decode()
                    return json.loads(text) if text else None
            except urllib.error.HTTPError as e:
                status = e.code
                if should_retry(status) and attempt < MAX_RETRIES:
                    try:
                        wait = int(e.headers.get("Retry-After", 2**attempt))
                    except (TypeError, ValueError):
                        wait = 2**attempt
                    time.sleep(min(wait, RETRY_AFTER_CAP))
                    attempt += 1
                    continue
                detail = e.read().decode(errors="replace")
                try:
                    message = json.loads(detail)["error"]["message"]
                except (ValueError, KeyError, TypeError):
                    message = detail or e.reason
                raise HttpError(str(message), status=status) from e
            except urllib.error.URLError as e:
                raise HttpError(str(e.reason), status=0) from e

    def request_all(self, url: str) -> dict:
        """Collection-only: follow @odata.nextLink, concatenating each page's `value`
        array into `{"value": [...]}`. Do not use for single-entity GETs."""
        combined: list = []
        nxt: str | None = url
        while nxt:
            page = self.request("GET", nxt)
            if isinstance(page, dict):
                values = page.get("value")
                if isinstance(values, list):
                    combined.extend(values)
                nxt = page.get(NEXT_LINK)
            else:
                nxt = None
        return {"value": combined}
