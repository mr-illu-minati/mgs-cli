from mgs.odata import NEXT_LINK, QueryOptions


def test_empty_query_is_empty_string():
    assert QueryOptions().to_query_string() == ""


def test_builds_select_filter_top_encoded():
    s = QueryOptions(select="subject,from", filter="isRead eq false", top=5).to_query_string()
    assert s.startswith("?")
    assert "%24select=subject%2Cfrom" in s
    assert "%24top=5" in s
    assert "%24filter=isRead+eq+false" in s


def test_next_link_constant():
    assert NEXT_LINK == "@odata.nextLink"
