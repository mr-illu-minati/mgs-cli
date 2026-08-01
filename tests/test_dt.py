from datetime import datetime

import pytest

from mgs.errors import UsageError
from mgs.helpers.dt import (
    build_attendees,
    day_window,
    find_conflicts,
    iso,
    parse_dt,
    to_graph,
)


def test_parse_dt_formats():
    assert parse_dt("2026-07-01T14:30") == datetime(2026, 7, 1, 14, 30)
    assert parse_dt("2026-07-01 14:30") == datetime(2026, 7, 1, 14, 30)
    assert parse_dt("2026-07-01T14:30:15") == datetime(2026, 7, 1, 14, 30, 15)
    assert parse_dt("2026-07-01") == datetime(2026, 7, 1, 0, 0)


def test_parse_dt_invalid():
    with pytest.raises(UsageError):
        parse_dt("next tuesday")


def test_iso_and_to_graph():
    dt = datetime(2026, 7, 1, 14, 30)
    assert iso(dt) == "2026-07-01T14:30:00"
    assert to_graph(dt, "UTC") == {"dateTime": "2026-07-01T14:30:00", "timeZone": "UTC"}


def test_day_window():
    start = datetime(2026, 7, 1, 9, 15)
    s, e = day_window(start, 1)
    assert s == datetime(2026, 7, 1, 0, 0)
    assert e == datetime(2026, 7, 2, 0, 0)
    _, e7 = day_window(start, 7)
    assert e7 == datetime(2026, 7, 8, 0, 0)


def test_build_attendees():
    assert build_attendees("a@x.com, b@y.com") == [
        {"emailAddress": {"address": "a@x.com"}, "type": "required"},
        {"emailAddress": {"address": "b@y.com"}, "type": "required"},
    ]
    assert build_attendees(None) == []


def test_find_conflicts():
    events = [
        {"subject": "Standup", "start": {"dateTime": "2026-07-01T09:00:00"},
         "end": {"dateTime": "2026-07-01T09:30:00"}},
        {"subject": "Lunch", "start": {"dateTime": "2026-07-01T12:00:00"},
         "end": {"dateTime": "2026-07-01T13:00:00"}},
    ]
    # 09:15-09:45 overlaps Standup, not Lunch
    hits = find_conflicts(datetime(2026, 7, 1, 9, 15), datetime(2026, 7, 1, 9, 45), events)
    assert [h["subject"] for h in hits] == ["Standup"]
    # 10:00-11:00 overlaps nothing
    assert find_conflicts(datetime(2026, 7, 1, 10, 0), datetime(2026, 7, 1, 11, 0), events) == []
