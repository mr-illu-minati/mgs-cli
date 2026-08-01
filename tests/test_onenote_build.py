from mgs.helpers.onenote_build import build_page_html, pages_path


def test_build_page_html_escapes_plain_text():
    html = build_page_html("My <Title>", "a & b", is_html=False)
    assert "<title>My &lt;Title&gt;</title>" in html
    assert "<p>a &amp; b</p>" in html


def test_build_page_html_passes_html_through():
    html = build_page_html("T", "<b>bold</b>", is_html=True)
    assert "<body><b>bold</b></body>" in html


def test_pages_path():
    assert pages_path(None) == "/me/onenote/pages"
    assert pages_path("1-abc") == "/me/onenote/sections/1-abc/pages"
