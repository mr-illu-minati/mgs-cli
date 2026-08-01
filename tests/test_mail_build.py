import base64

import pytest

from mgs.errors import UsageError, ValidationError
from mgs.helpers.mail_build import (
    build_message,
    file_attachment,
    html_to_text,
    parse_recipients,
)


def test_parse_recipients():
    assert parse_recipients("a@x.com, b@y.com") == [
        {"emailAddress": {"address": "a@x.com"}},
        {"emailAddress": {"address": "b@y.com"}},
    ]
    assert parse_recipients("") == []


def test_build_message_text():
    m = build_message("Hi", "Body", html=False, to="a@x.com", cc=None, bcc=None, attach=None)
    assert m["subject"] == "Hi"
    assert m["body"] == {"contentType": "Text", "content": "Body"}
    assert m["toRecipients"] == [{"emailAddress": {"address": "a@x.com"}}]


def test_build_message_html_and_cc():
    m = build_message("Hi", "<b>x</b>", html=True, to="a@x.com", cc="c@x.com", bcc=None, attach=None)
    assert m["body"]["contentType"] == "HTML"
    assert m["ccRecipients"] == [{"emailAddress": {"address": "c@x.com"}}]


def test_file_attachment(tmp_path):
    f = tmp_path / "note.txt"
    f.write_bytes(b"hello")
    att = file_attachment(str(f))
    assert att["@odata.type"] == "#microsoft.graph.fileAttachment"
    assert att["name"] == "note.txt"
    assert base64.b64decode(att["contentBytes"]) == b"hello"


def test_attachment_missing_file_is_usage_error():
    with pytest.raises(UsageError):
        file_attachment("/no/such/file.bin")


def test_build_message_requires_recipients():
    with pytest.raises(UsageError):
        build_message("Hi", "Body", html=False, to=None, cc=None, bcc=None, attach=None)


def test_html_to_text():
    assert html_to_text("<p>Hi <b>there</b></p><br>x") == "Hi there\nx"
    assert html_to_text("a &amp; b") == "a & b"
