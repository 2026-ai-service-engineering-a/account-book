from __future__ import annotations

from ui.interfaces.ai_map import SEATS


def test_wiki_has_a_section_per_seat(client):
    page = client.get("/wiki")
    assert page.status_code == 200
    for seat in SEATS:
        assert f'id="{seat.key}"' in page.text
        assert seat.stand_in in page.text  # 지금 무엇이 서 있는지 말한다
    for anchor in ("overview", "architecture", "flows", "principles", "tools", "mcp", "stand-ins"):
        assert f'id="{anchor}"' in page.text


def test_wiki_says_ai_is_not_attached_yet(client):
    assert "지금은 AI가 붙어 있지 않다." in client.get("/wiki").text


def test_header_links_to_wiki_everywhere(client):
    for path in ("/", "/transactions", "/budgets"):
        assert 'class="wiki-link" href="/wiki"' in client.get(path).text
    assert 'href="/wiki" aria-current="page"' in client.get("/wiki").text
