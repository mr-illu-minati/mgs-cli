from mgs.commands import build_service_parser
from mgs.services import resolve


def test_create_has_json_and_params():
    p = build_service_parser(resolve("mail"))
    ns = p.parse_args(["create", "--json", '{"subject":"x"}', "--dry-run"])
    assert ns.verb == "create"
    assert ns.json == '{"subject":"x"}'
    assert ns.dry_run is True


def test_update_takes_id_and_json():
    p = build_service_parser(resolve("mail"))
    ns = p.parse_args(["update", "AAA", "--json", '{"isRead":true}'])
    assert ns.verb == "update"
    assert ns.id == "AAA"


def test_delete_takes_id():
    p = build_service_parser(resolve("mail"))
    ns = p.parse_args(["delete", "AAA"])
    assert ns.verb == "delete"
    assert ns.id == "AAA"


def test_list_has_search_and_folder():
    p = build_service_parser(resolve("mail"))
    ns = p.parse_args(["list", "--search", '"hi"', "--folder", "inbox"])
    assert ns.search == '"hi"'
    assert ns.folder == "inbox"
