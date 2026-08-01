import pytest

from mgs.errors import ValidationError
from mgs.validate import encode_path_segment, validate_resource_name


def test_encode_spaces_and_slashes():
    assert encode_path_segment("a b/c") == "a%20b%2Fc"


def test_resource_name_accepts_normal_id():
    assert validate_resource_name("AAMkAD-Rm9AABDGisXAAA=") == "AAMkAD-Rm9AABDGisXAAA="


@pytest.mark.parametrize("bad", ["../etc", "a?b", "a#b", "a\nb", "a\\b", ""])
def test_resource_name_rejects_bad(bad):
    with pytest.raises(ValidationError):
        validate_resource_name(bad)
