"""Parse Graph CSDL ($metadata) and cache it as compact per-EntityType JSON.

A normal invocation needs one EntityType, so it reads a few-KB JSON file rather than
re-parsing the ~2.7 MB XML. The XML is fetched + parsed at most once per 24h (cache miss).
"""

from __future__ import annotations

import io
import json
import os
import time
import urllib.request
import xml.etree.ElementTree as ET

from mgs.errors import MetadataError
from mgs.metadata import EntityType, Metadata, NavigationProperty, Operation, Property

V1_METADATA_URL = "https://graph.microsoft.com/v1.0/$metadata"
BETA_METADATA_URL = "https://graph.microsoft.com/beta/$metadata"
CACHE_TTL = 24 * 60 * 60


def _local(tag: str) -> str:
    """Strip the `{namespace}` prefix ElementTree prepends to qualified tags."""
    return tag.rsplit("}", 1)[-1]


def _unwrap_collection(type_name: str) -> tuple[str, bool]:
    if type_name.startswith("Collection(") and type_name.endswith(")"):
        return type_name[len("Collection("):-1], True
    return type_name, False


def parse_edmx(xml_text: str) -> Metadata:
    """Stream-parse an EDMX/CSDL document into a Metadata model."""
    md = Metadata()
    cur_entity: EntityType | None = None
    cur_op: Operation | None = None
    cur_ns = ""

    for event, elem in ET.iterparse(io.StringIO(xml_text), events=("start", "end")):
        tag = _local(elem.tag)
        if event == "start":
            if tag == "Schema":
                cur_ns = elem.get("Namespace", "")
            elif tag == "EntityType":
                cur_entity = EntityType(name=elem.get("Name", ""), namespace=cur_ns)
            elif tag in ("Action", "Function"):
                cur_op = Operation(name=elem.get("Name", ""))
            elif tag == "Property":
                name, ty = elem.get("Name"), elem.get("Type")
                if name and ty:
                    prop = Property(name, ty, elem.get("Nullable", "true") == "true")
                    if cur_op is not None:
                        cur_op.parameters.append(prop)
                    elif cur_entity is not None:
                        cur_entity.properties.append(prop)
            elif tag == "NavigationProperty":
                name, ty = elem.get("Name"), elem.get("Type")
                if name and ty and cur_entity is not None:
                    _, collection = _unwrap_collection(ty)
                    cur_entity.navigations.append(NavigationProperty(name, ty, collection))
            elif tag == "Parameter":
                name, ty = elem.get("Name"), elem.get("Type")
                if name and ty and cur_op is not None:
                    if name in ("bindingParameter", "bindParameter"):
                        inner, _ = _unwrap_collection(ty)
                        cur_op.bound_to = inner.rsplit(".", 1)[-1]
                    else:
                        cur_op.parameters.append(Property(name, ty, True))
        else:  # end
            if tag == "EntityType" and cur_entity is not None:
                md.entity_types.append(cur_entity)
                cur_entity = None
            elif tag == "Action" and cur_op is not None:
                md.actions.append(cur_op)
                cur_op = None
            elif tag == "Function" and cur_op is not None:
                md.functions.append(cur_op)
                cur_op = None
            elif tag == "Schema":
                cur_ns = ""
            elem.clear()
    return md


def _meta_dir(config_dir: str, beta: bool) -> str:
    return os.path.join(config_dir, "metadata", "beta" if beta else "v1")


def _cache_fresh(stamp_path: str) -> bool:
    try:
        return (time.time() - os.path.getmtime(stamp_path)) < CACHE_TTL
    except OSError:
        return False


def _et_to_dict(et: EntityType) -> dict:
    return {
        "name": et.name,
        "namespace": et.namespace,
        "properties": [[p.name, p.type_name, p.nullable] for p in et.properties],
        "navigations": [[n.name, n.type_name, n.collection] for n in et.navigations],
    }


def _et_from_dict(d: dict) -> EntityType:
    return EntityType(
        name=d["name"],
        namespace=d.get("namespace", ""),
        properties=[Property(*p) for p in d["properties"]],
        navigations=[NavigationProperty(*n) for n in d["navigations"]],
    )


def _refresh(config_dir: str, beta: bool) -> None:
    """Fetch + parse $metadata once, writing compact per-type JSON + an operations index."""
    url = BETA_METADATA_URL if beta else V1_METADATA_URL
    req = urllib.request.Request(url, headers={"Accept": "application/xml"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            xml_text = resp.read().decode("utf-8")
    except OSError as e:
        raise MetadataError(f"failed to fetch metadata: {e}") from e

    md = parse_edmx(xml_text)
    d = _meta_dir(config_dir, beta)
    types_dir = os.path.join(d, "types")
    os.makedirs(types_dir, exist_ok=True)

    # Prefer the microsoft.graph namespace on unqualified-name collisions.
    chosen: dict[str, EntityType] = {}
    for et in md.entity_types:
        key = et.name.lower()
        if key not in chosen or et.namespace == "microsoft.graph":
            chosen[key] = et
    for et in chosen.values():
        safe = et.name.replace("/", "_").replace("\\", "_")
        with open(os.path.join(types_dir, f"{safe}.json"), "w") as f:
            json.dump(_et_to_dict(et), f)

    ops: dict[str, list] = {}
    for op in (*md.actions, *md.functions):
        if op.bound_to:
            ops.setdefault(op.bound_to.lower(), []).append(
                {"name": op.name, "parameters": [[p.name, p.type_name] for p in op.parameters]}
            )
    with open(os.path.join(d, "operations.json"), "w") as f:
        json.dump(ops, f)
    with open(os.path.join(d, ".stamp"), "w") as f:
        f.write(str(time.time()))


def load_entity_type(config_dir: str, name: str, beta: bool = False) -> EntityType | None:
    """Load one EntityType from the compact cache, refreshing from the network if stale."""
    d = _meta_dir(config_dir, beta)
    if not _cache_fresh(os.path.join(d, ".stamp")):
        _refresh(config_dir, beta)
    safe = name.replace("/", "_").replace("\\", "_")
    path = os.path.join(d, "types", f"{safe}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return _et_from_dict(json.load(f))


def load_operations_bound_to(config_dir: str, type_name: str, beta: bool = False) -> list[dict]:
    """Load the bound-operations index entry for an EntityType (compact cache)."""
    d = _meta_dir(config_dir, beta)
    if not _cache_fresh(os.path.join(d, ".stamp")):
        _refresh(config_dir, beta)
    path = os.path.join(d, "operations.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f).get(type_name.lower(), [])
