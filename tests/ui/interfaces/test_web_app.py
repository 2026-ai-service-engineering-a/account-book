from __future__ import annotations

import dataclasses

from fastapi.testclient import TestClient

from tests.ui.conftest import FixedClock
from ui.main import create_app


class BrokenReports:
    async def totals(self, criteria):
        raise RuntimeError("SELECT * FROM secret")


def test_unknown_page_is_404_page(empty_client):
    page = empty_client.get("/nope")
    assert page.status_code == 404 and "페이지를 찾지 못했어요." in page.text


def test_500_hides_internals_and_shows_request_id():
    app = create_app(clock=FixedClock(), seeded=False)
    app.state.services = dataclasses.replace(app.state.services, reports=BrokenReports())
    page = TestClient(app, raise_server_exceptions=False).get("/")
    assert page.status_code == 500
    assert "문제가 생겼어요." in page.text and "secret" not in page.text
    assert "요청 id" in page.text


def test_static_files_are_served(empty_client):
    assert empty_client.get("/static/chat.js").status_code == 200
    assert empty_client.get("/static/htmx.min.js").status_code == 200


def test_ledger_unavailable_is_a_503_page():
    import dataclasses

    from fastapi.testclient import TestClient

    from tests.ui.conftest import FixedClock
    from ui.application.errors import LedgerUnavailable
    from ui.main import create_app

    class Down:
        async def exists_any(self) -> bool:
            raise LedgerUnavailable("ConnectError")

        async def search(self, *args, **kwargs):
            raise LedgerUnavailable("ConnectError")

    app = create_app(clock=FixedClock(), seeded=False)
    app.state.services = dataclasses.replace(app.state.services, transactions=Down())
    page = TestClient(app).get("/transactions")
    assert page.status_code == 503 and "가계부 서버에 닿지 못했어요" in page.text
