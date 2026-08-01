import argparse

from mgs.executor import opts_from_namespace
from mgs.helpers import calendar  # noqa: F401  (registers helpers)
from mgs.helpers import registry
from mgs.helpers.calendar import build_event, render_event


def _run(verb, args):
    helper = registry.get("event", verb)
    p = argparse.ArgumentParser()
    helper.add_arguments(p)
    ns = p.parse_args(args)
    return helper.run("", ns, opts_from_namespace(ns))


def test_agenda_registered():
    assert registry.get("event", "+agenda") is not None
    assert registry.get("event", "+insert") is not None


def test_agenda_dry_run_uses_calendarview():
    out = _run("+agenda", ["--start", "2026-07-01", "--days", "1", "--timezone", "UTC", "--dry-run"])
    assert out["method"] == "GET"
    assert "/me/calendarView" in out["url"]
    assert "startDateTime=2026-07-01T00%3A00%3A00" in out["url"]
    assert "endDateTime=2026-07-02T00%3A00%3A00" in out["url"]


def test_agenda_week_window():
    out = _run("+agenda", ["--start", "2026-07-01", "--week", "--dry-run"])
    assert "endDateTime=2026-07-08T00%3A00%3A00" in out["url"]


def test_render_event():
    ev = {
        "subject": "Sync", "isAllDay": False, "isOnlineMeeting": True,
        "start": {"dateTime": "2026-07-01T09:00:00.0000000"},
        "end": {"dateTime": "2026-07-01T09:30:00.0000000"},
        "location": {"displayName": "Room 4"},
        "organizer": {"emailAddress": {"name": "Al", "address": "al@x.com"}},
        "attendees": [{}, {}],
    }
    r = render_event(ev)
    assert r == {
        "start": "2026-07-01T09:00:00.0000000", "end": "2026-07-01T09:30:00.0000000",
        "subject": "Sync", "location": "Room 4", "organizer": "Al <al@x.com>",
        "attendees": 2, "isAllDay": False, "isOnline": True,
    }


def test_build_event_with_duration():
    ev, s, e = build_event(
        subject="Sync", start="2026-07-01T14:00", end=None, duration=30, tz="UTC",
        attendees="a@x.com", location="Room 4", body="agenda", all_day=False, online=True,
    )
    assert ev["subject"] == "Sync"
    assert ev["start"] == {"dateTime": "2026-07-01T14:00:00", "timeZone": "UTC"}
    assert ev["end"] == {"dateTime": "2026-07-01T14:30:00", "timeZone": "UTC"}
    assert ev["isOnlineMeeting"] is True
    assert ev["location"] == {"displayName": "Room 4"}
    assert ev["attendees"][0]["emailAddress"]["address"] == "a@x.com"


def test_build_event_explicit_end_overrides_duration():
    ev, s, e = build_event(
        subject="X", start="2026-07-01T14:00", end="2026-07-01T15:30", duration=30, tz="UTC",
        attendees=None, location=None, body=None, all_day=False, online=False,
    )
    assert ev["end"]["dateTime"] == "2026-07-01T15:30:00"


def test_insert_dry_run_shows_event_no_conflict_call():
    out = _run("+insert", ["--subject", "Sync", "--start", "2026-07-01T14:00",
                           "--duration", "30", "--no-conflict-check", "--dry-run"])
    assert out["method"] == "POST"
    assert out["url"].endswith("/me/events")
    assert out["body"]["subject"] == "Sync"
