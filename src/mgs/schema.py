"""mgs schema <service> — introspect an EntityType from the compact metadata cache."""

from __future__ import annotations

from mgs import csdl
from mgs.errors import MetadataError
from mgs.metadata import EntityType
from mgs.services import ServiceEntry


def schema_from(entity_type: EntityType, operations: list[dict]) -> dict:
    return {
        "entityType": entity_type.name,
        "properties": [
            {"name": p.name, "type": p.type_name, "nullable": p.nullable}
            for p in entity_type.properties
        ],
        "navigations": [
            {"name": n.name, "type": n.type_name, "collection": n.collection}
            for n in entity_type.navigations
        ],
        "operations": [
            {
                "name": o["name"],
                "parameters": [{"name": pn, "type": pt} for pn, pt in o["parameters"]],
            }
            for o in operations
        ],
    }


def schema_value(config_dir: str, svc: ServiceEntry, beta: bool = False) -> dict:
    et = csdl.load_entity_type(config_dir, svc.entity_type, beta)
    if et is None:
        raise MetadataError(f"unknown entity type: {svc.entity_type}")
    ops = csdl.load_operations_bound_to(config_dir, svc.entity_type, beta)
    return schema_from(et, ops)
