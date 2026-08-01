"""Registry of +verb helper commands, keyed by (entity_type, "+verb")."""

from __future__ import annotations

_HELPERS: dict[tuple[str, str], object] = {}


def register(helper) -> None:
    _HELPERS[(helper.service, helper.name)] = helper


def get(entity_type: str, verb: str | None):
    if verb is None:
        return None
    return _HELPERS.get((entity_type, verb))


def for_service(entity_type: str) -> list:
    return [h for (et, _), h in _HELPERS.items() if et == entity_type]
