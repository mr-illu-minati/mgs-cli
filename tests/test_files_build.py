from mgs.helpers.files_build import (
    SMALL_MAX,
    compute_chunks,
    is_small,
    normalize_chunk_size,
    resolve_remote_path,
    session_body,
    upload_content_path,
    upload_session_path,
)


def test_resolve_remote_path():
    assert resolve_remote_path("/x/report.pdf", None, None) == "/report.pdf"
    assert resolve_remote_path("/x/report.pdf", "/Docs", None) == "/Docs/report.pdf"
    assert resolve_remote_path("/x/report.pdf", "/Docs/", None) == "/Docs/report.pdf"
    assert resolve_remote_path("/x/report.pdf", "/Docs/final.pdf", None) == "/Docs/final.pdf"
    assert resolve_remote_path("/x/report.pdf", None, "renamed.pdf") == "/renamed.pdf"


def test_upload_paths_encode():
    assert upload_content_path("/A B/c.txt") == "/me/drive/root:/A%20B/c.txt:/content"
    assert upload_session_path("/c.txt") == "/me/drive/root:/c.txt:/createUploadSession"


def test_is_small():
    assert is_small(SMALL_MAX)
    assert not is_small(SMALL_MAX + 1)


def test_normalize_chunk_size_multiple_of_320kib():
    assert normalize_chunk_size(10) == 10 * 1024 * 1024  # exact multiple
    assert normalize_chunk_size(0) == 327680  # floor to one unit minimum
    assert normalize_chunk_size(5) % 327680 == 0


def test_compute_chunks():
    assert compute_chunks(10, 4) == [(0, 3), (4, 7), (8, 9)]
    assert compute_chunks(8, 4) == [(0, 3), (4, 7)]


def test_session_body():
    assert session_body() == {"item": {"@microsoft.graph.conflictBehavior": "replace"}}
