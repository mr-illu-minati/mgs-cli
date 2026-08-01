from mgs.services import all_services, resolve


def test_resolves_known_aliases():
    assert resolve("mail").root_path == "/me/messages"
    assert resolve("messages").entity_type == "message"
    assert resolve("calendar").entity_type == "event"
    assert resolve("files").root_path == "/me/drive/root/children"
    assert resolve("users").entity_type == "user"


def test_unknown_alias_is_none():
    assert resolve("nope") is None


def test_all_services_lists_primary_names():
    assert any(s.aliases[0] == "mail" for s in all_services())


def test_teams_service():
    from mgs.services import resolve
    assert resolve("teams").entity_type == "team"
    assert resolve("teams").root_path == "/me/joinedTeams"
