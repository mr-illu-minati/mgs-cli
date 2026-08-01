"""Parsed CSDL data model. Plain dataclasses; populated by csdl.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Property:
    name: str
    type_name: str
    nullable: bool = True


@dataclass
class NavigationProperty:
    name: str
    type_name: str
    collection: bool = False


@dataclass
class EntityType:
    name: str
    namespace: str = ""
    properties: list[Property] = field(default_factory=list)
    navigations: list[NavigationProperty] = field(default_factory=list)


@dataclass
class Operation:
    name: str
    bound_to: str | None = None
    parameters: list[Property] = field(default_factory=list)


@dataclass
class Metadata:
    entity_types: list[EntityType] = field(default_factory=list)
    actions: list[Operation] = field(default_factory=list)
    functions: list[Operation] = field(default_factory=list)

    def entity_type(self, name: str) -> EntityType | None:
        """Look up by unqualified name (case-insensitive), preferring the
        `microsoft.graph` namespace when several namespaces share the name."""
        matches = [e for e in self.entity_types if e.name.lower() == name.lower()]
        if not matches:
            return None
        for e in matches:
            if e.namespace == "microsoft.graph":
                return e
        return matches[0]

    def operations_bound_to(self, type_name: str) -> Iterator[Operation]:
        for op in (*self.actions, *self.functions):
            if op.bound_to and op.bound_to.lower() == type_name.lower():
                yield op
