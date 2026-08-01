from mgs.helpers.excel_build import (
    append_path,
    coerce_values,
    read_range_path,
    workbook_base,
)


def test_workbook_base_by_id_and_path():
    assert workbook_base("01ABC") == "/me/drive/items/01ABC/workbook"
    assert workbook_base("/Book.xlsx") == "/me/drive/root:/Book.xlsx:/workbook"


def test_read_range_path():
    assert read_range_path("01ABC", "Sheet1", None) == (
        "/me/drive/items/01ABC/workbook/worksheets('Sheet1')/usedRange")
    assert read_range_path("01ABC", "Sheet1", "A1:C2") == (
        "/me/drive/items/01ABC/workbook/worksheets('Sheet1')/range(address='A1%3AC2')")


def test_append_path():
    assert append_path("01ABC", "Table1") == (
        "/me/drive/items/01ABC/workbook/tables/Table1/rows/add")


def test_coerce_values():
    assert coerce_values("a, 1, 2.5, b") == [["a", 1, 2.5, "b"]]
