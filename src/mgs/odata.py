"""OData system query options -> query string, plus the nextLink field name."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

NEXT_LINK = "@odata.nextLink"


@dataclass
class QueryOptions:
    select: str | None = None
    filter: str | None = None
    orderby: str | None = None
    expand: str | None = None
    search: str | None = None
    top: int | None = None
    skip: int | None = None

    def to_query_string(self) -> str:
        pairs: list[tuple[str, str]] = []
        if self.select:
            pairs.append(("$select", self.select))
        if self.filter:
            pairs.append(("$filter", self.filter))
        if self.orderby:
            pairs.append(("$orderby", self.orderby))
        if self.expand:
            pairs.append(("$expand", self.expand))
        if self.search:
            pairs.append(("$search", self.search))
        if self.top is not None:
            pairs.append(("$top", str(self.top)))
        if self.skip is not None:
            pairs.append(("$skip", str(self.skip)))
        if not pairs:
            return ""
        return "?" + "&".join(f"{quote_plus(k)}={quote_plus(v)}" for k, v in pairs)
