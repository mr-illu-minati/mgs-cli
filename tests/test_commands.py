from mgs.commands import build_service_parser
from mgs.services import resolve


def test_list_parses_odata_flags():
    p = build_service_parser(resolve("mail"))
    ns = p.parse_args(["list", "--top", "5", "--select", "subject", "--dry-run", "--page-all"])
    assert ns.verb == "list"
    assert ns.top == 5
    assert ns.select == "subject"
    assert ns.dry_run is True
    assert ns.page_all is True


def test_get_requires_id():
    p = build_service_parser(resolve("users"))
    ns = p.parse_args(["get", "alice@example.com"])
    assert ns.verb == "get"
    assert ns.id == "alice@example.com"
