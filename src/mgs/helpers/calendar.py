"""Outlook calendar +verb helpers (agenda, insert), matching the gws Calendar set."""

from __future__ import annotations

import argparse
from datetime import datetime
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

from mgs.executor import Opts
from mgs.helpers import dt, registry
from mgs.userpath import resolve_user_path

_AGENDA_SELECT = "subject,start,end,location,organizer,attendees,isAllDay,isOnlineMeeting"


def _addr(person: dict) -> str:
    e = (person or {}).get("emailAddress", {})
    name, address = e.get("name"), e.get("address", "")
    return f"{name} <{address}>" if name else address


def render_event(ev: dict) -> dict:
    return {
        "start": ev.get("start", {}).get("dateTime"),
        "end": ev.get("end", {}).get("dateTime"),
        "subject": ev.get("subject"),
        "location": (ev.get("location") or {}).get("displayName"),
        "organizer": _addr(ev.get("organizer")),
        "attendees": len(ev.get("attendees", []) or []),
        "isAllDay": ev.get("isAllDay", False),
        "isOnline": ev.get("isOnlineMeeting", False),
    }


def _now_naive(tz: str) -> datetime:
    return datetime.now(ZoneInfo(tz)).replace(tzinfo=None, second=0, microsecond=0)


def _calendarview_path(start: datetime, end: datetime, top: int) -> str:
    params = {
        "startDateTime": dt.iso(start),
        "endDateTime": dt.iso(end),
        "$orderby": "start/dateTime",
        "$top": str(top),
        "$select": _AGENDA_SELECT,
    }
    query = "&".join(f"{quote_plus(k)}={quote_plus(v)}" for k, v in params.items())
    return f"/me/calendarView?{query}"


class AgendaHelper:
    name = "+agenda"
    service = "event"
    help = "Show upcoming events (calendarView; expands recurrences)"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--start", help="Window start date YYYY-MM-DD (default: today)")
        p.add_argument("--days", type=int, default=1, help="Days to show (default 1 = today)")
        p.add_argument("--week", action="store_true", help="Show the next 7 days")
        p.add_argument("--timezone", default="UTC", help="IANA timezone (default UTC)")
        p.add_argument("--max", type=int, default=50, help="Max events to return")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        tz = ns.timezone or "UTC"
        start = dt.parse_dt(ns.start) if ns.start else _now_naive(tz)
        days = 7 if ns.week else ns.days
        s, e = dt.day_window(start, days)
        path = resolve_user_path(_calendarview_path(s, e, ns.max))
        if opts.dry_run:
            version = "beta" if opts.beta else "v1.0"
            return {
                "dryRun": True,
                "method": "GET",
                "url": f"https://graph.microsoft.com/{version}{path}",
            }
        from mgs.client import GraphClient

        client = GraphClient(token, beta=opts.beta)
        resp = client.request(
            "GET", client.full_url(path), headers={"Prefer": f'outlook.timezone="{tz}"'}
        )
        events = resp.get("value", []) if isinstance(resp, dict) else []
        return {
            "window": {"start": dt.iso(s), "end": dt.iso(e), "timezone": tz},
            "count": len(events),
            "events": [render_event(ev) for ev in events],
        }


registry.register(AgendaHelper())


def build_event(
    *,
    subject: str,
    start: str,
    end: str | None,
    duration: int,
    tz: str,
    attendees: str | None,
    location: str | None,
    body: str | None,
    all_day: bool,
    online: bool,
) -> tuple[dict, datetime, datetime]:
    from datetime import timedelta

    s_dt = dt.parse_dt(start)
    e_dt = dt.parse_dt(end) if end else s_dt + timedelta(minutes=duration)
    event: dict = {
        "subject": subject or "",
        "start": dt.to_graph(s_dt, tz),
        "end": dt.to_graph(e_dt, tz),
    }
    if all_day:
        event["isAllDay"] = True
    if location:
        event["location"] = {"displayName": location}
    if body:
        event["body"] = {"contentType": "Text", "content": body}
    if online:
        event["isOnlineMeeting"] = True
    atts = dt.build_attendees(attendees)
    if atts:
        event["attendees"] = atts
    return event, s_dt, e_dt


class InsertHelper:
    name = "+insert"
    service = "event"
    help = "Create a calendar event (conflict-checked unless --no-conflict-check)"

    def add_arguments(self, p: argparse.ArgumentParser) -> None:
        p.add_argument("--subject", default="", help="Event subject")
        p.add_argument("--start", required=True, help="ISO start, e.g. 2026-07-01T14:00")
        p.add_argument("--end", help="ISO end (overrides --duration)")
        p.add_argument("--duration", type=int, default=30, help="Minutes (default 30)")
        p.add_argument("--attendees", help="Comma-separated emails")
        p.add_argument("--location", help="Event location")
        p.add_argument("--body", help="Event body/notes")
        p.add_argument("--all-day", action="store_true", help="Create an all-day event")
        p.add_argument("--online", action="store_true", help="Create a Teams online meeting")
        p.add_argument("--timezone", default="UTC", help="IANA timezone (default UTC)")
        p.add_argument("--no-conflict-check", action="store_true", help="Skip the overlap check")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--beta", action="store_true")

    def run(self, token: str, ns: argparse.Namespace, opts: Opts) -> object:
        event, s_dt, e_dt = build_event(
            subject=ns.subject,
            start=ns.start,
            end=ns.end,
            duration=ns.duration,
            tz=ns.timezone,
            attendees=ns.attendees,
            location=ns.location,
            body=ns.body,
            all_day=ns.all_day,
            online=ns.online,
        )
        events_path = resolve_user_path("/me/events")
        if opts.dry_run:
            version = "beta" if opts.beta else "v1.0"
            return {
                "dryRun": True,
                "method": "POST",
                "url": f"https://graph.microsoft.com/{version}{events_path}",
                "body": event,
            }

        from mgs.client import GraphClient

        client = GraphClient(token, beta=opts.beta)
        conflicts = []
        if not ns.no_conflict_check:
            path = _calendarview_path(s_dt, e_dt, 50)
            resp = client.request(
                "GET",
                client.full_url(path),
                headers={"Prefer": f'outlook.timezone="{ns.timezone}"'},
            )
            value = resp.get("value", []) if isinstance(resp, dict) else []
            conflicts = dt.find_conflicts(s_dt, e_dt, value)
        created = client.request("POST", client.full_url(events_path), body=event)
        result = {
            "created": created.get("id") if isinstance(created, dict) else None,
            "event": render_event(created if isinstance(created, dict) else event),
        }
        if conflicts:
            result["conflicts"] = conflicts
        return result


registry.register(InsertHelper())
