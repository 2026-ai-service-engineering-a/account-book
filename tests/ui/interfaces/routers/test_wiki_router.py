from __future__ import annotations

import dataclasses

from fastapi.testclient import TestClient

from tests.ui.conftest import FixedClock
from ui.interfaces.ai_map import SEATS
from ui.main import create_app


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


def test_wiki_says_which_seats_run_on_the_agent():
    app = create_app(clock=FixedClock(), seeded=False)
    app.state.services = dataclasses.replace(app.state.services, live_seats=frozenset({"capture"}))
    page = TestClient(app).get("/wiki").text
    capture = next(s for s in SEATS if s.key == "capture")
    assert "AI가 일부 자리에 붙어 있다." in page and capture.live in page


def test_header_links_to_wiki_everywhere(client):
    for path in ("/", "/transactions", "/budgets"):
        assert 'class="wiki-link" href="/wiki"' in client.get(path).text
    assert 'href="/wiki" aria-current="page"' in client.get("/wiki").text
