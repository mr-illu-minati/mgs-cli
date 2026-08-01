"""Alias -> Graph root path + root EntityType registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceEntry:
    aliases: tuple[str, ...]
    root_path: str
    entity_type: str
    description: str


SERVICES: tuple[ServiceEntry, ...] = (
    ServiceEntry(
        ("mail", "messages"), "/me/messages", "message", "Read, send, and manage Outlook mail"
    ),
    ServiceEntry(("calendar", "events"), "/me/events", "event", "Manage Outlook calendar events"),
    ServiceEntry(
        ("files", "drive"),
        "/me/drive/root/children",
        "driveItem",
        "Browse and manage OneDrive/SharePoint files",
    ),
    ServiceEntry(("users", "people"), "/users", "user", "Look up users in the directory"),
    ServiceEntry(
        ("teams", "team"), "/me/joinedTeams", "team", "Microsoft Teams: teams, channels, messages"
    ),
    ServiceEntry(
        ("excel", "workbook"),
        "/me/drive/root/children",
        "workbook",
        "Excel workbooks (helpers: +read/+append)",
    ),
    ServiceEntry(("onenote", "notes"), "/me/onenote/pages", "onenotePage", "OneNote pages"),
)


def resolve(alias: str) -> ServiceEntry | None:
    low = alias.lower()
    for s in SERVICES:
        if low in (a.lower() for a in s.aliases):
            return s
    return None


def all_services() -> tuple[ServiceEntry, ...]:
    return SERVICES
