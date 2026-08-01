import pytest

from mgs.drivepath import drive_item_base, encode_drive_path, is_path_ref
from mgs.errors import ValidationError


def test_is_path_ref():
    assert is_path_ref("/Reports/Q3.xlsx")
    assert not is_path_ref("01ABCDEF")


def test_encode_drive_path_keeps_slashes_encodes_segments():
    assert encode_drive_path("/Reports/Q3 Budget.xlsx") == "/Reports/Q3%20Budget.xlsx"


def test_drive_item_base_by_path_and_id():
    assert drive_item_base("/Reports/Q3.xlsx") == "/me/drive/root:/Reports/Q3.xlsx:"
    assert drive_item_base("01ABC") == "/me/drive/items/01ABC"


def test_drive_item_base_rejects_traversal():
    with pytest.raises(ValidationError):
        drive_item_base("/a/../secret")
