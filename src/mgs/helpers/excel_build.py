"""Pure builders for Excel workbook paths and values."""

from __future__ import annotations

from urllib.parse import quote

from mgs.drivepath import drive_item_base


def _q(value: str) -> str:
    return quote(value, safe="")


def workbook_base(file_ref: str) -> str:
    return drive_item_base(file_ref) + "/workbook"


def read_range_path(file_ref: str, sheet: str, address: str | None) -> str:
    ws = f"{workbook_base(file_ref)}/worksheets('{_q(sheet)}')"
    if address:
        return f"{ws}/range(address='{_q(address)}')"
    return f"{ws}/usedRange"


def append_path(file_ref: str, table: str) -> str:
    return f"{workbook_base(file_ref)}/tables/{_q(table)}/rows/add"


def coerce_values(raw: str) -> list[list]:
    """'a, 1, 2.5' -> [["a", 1, 2.5]] (single row, numbers coerced)."""
    row: list = []
    for part in raw.split(","):
        s = part.strip()
        try:
            row.append(int(s))
            continue
        except ValueError:
            pass
        try:
            row.append(float(s))
            continue
        except ValueError:
            pass
        row.append(s)
    return [row]
