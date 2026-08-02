from mgs.client import GraphClient, should_retry


def test_full_url_joins_base_path_query():
    c = GraphClient("tok", beta=False)
    assert (
        c.full_url("/me/messages", "?%24top=5")
        == "https://graph.microsoft.com/v1.0/me/messages?%24top=5"
    )


def test_beta_base_url():
    c = GraphClient("tok", beta=True)
    assert c.full_url("/me", "") == "https://graph.microsoft.com/beta/me"


def test_full_url_swaps_me_for_mailbox(monkeypatch):
    monkeypatch.setenv("MGS_MAILBOX", "shared@contoso.com")
    c = GraphClient("tok", beta=False)
    assert (
        c.full_url("/me/messages", "?%24top=5")
        == "https://graph.microsoft.com/v1.0/users/shared%40contoso.com/messages?%24top=5"
    )


def test_retry_decision():
    assert should_retry(429)
    assert should_retry(503)
    assert not should_retry(404)
    assert not should_retry(200)
