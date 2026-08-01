"""Pure datetime helpers for calendar commands (parse, window, event-time, conflicts)."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from mgs.errors import UsageError

_FORMATS = ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d")


def parse_dt(value: str) -> datetime:
    """Parse a human-ish datetime into a naive datetime. Accepts space or 'T' separator."""
    s = value.strip().replace(" ", "T")
    for fmt in _FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise UsageError(f"invalid datetime {value!r}; use YYYY-MM-DDTHH:MM")


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def to_graph(dt: datetime, tz: str) -> dict:
    return {"dateTime": iso(dt), "timeZone": tz}


def day_window(start: datetime, days: int) -> tuple[datetime, datetime]:
    """Midnight-aligned window: [start's date 00:00, +days)."""
    s = datetime.combine(start.date(), time(0, 0))
    return s, s + timedelta(days=days)


def build_attendees(raw: str | None) -> list[dict]:
    if not raw:
        return []
    out = []
    for part in raw.split(","):
        addr = part.strip()
        if addr:
            out.append({"emailAddress": {"address": addr}, "type": "required"})
    return out


def _event_bounds(ev: dict) -> tuple[datetime, datetime] | None:
    try:
        s = parse_dt(ev["start"]["dateTime"][:19])
        e = parse_dt(ev["end"]["dateTime"][:19])
        return s, e
    except (KeyError, TypeError, UsageError):
        return None


def find_conflicts(start: datetime, end: datetime, events: list[dict]) -> list[dict]:
    """Events whose interval overlaps [start, end). Returns compact {subject,start,end}."""
    hits = []
    for ev in events:
        bounds = _event_bounds(ev)
        if bounds is None:
            continue
        s, e = bounds
        if s < end and e > start:
            hits.append({
                "subject": ev.get("subject"),
                "start": ev.get("start", {}).get("dateTime"),
                "end": ev.get("end", {}).get("dateTime"),
            })
    return hits
