from __future__ import annotations

import dataclasses
from datetime import datetime

from fastapi.testclient import TestClient

from tests.ui.application.dto.test_run_line import line
from tests.ui.conftest import SEOUL, FixedClock
from ui.application.dto import RunCall, RunDetail, RunFilter, RunPage
from ui.application.errors import LedgerUnavailable
from ui.application.values import PageCursor, RunId
from ui.main import create_app

INSIGHT = line("r1")
CAPTURE = line("r2", seat="capture", flow="single", utterance="어제 점심 김밥천국 8500원",
               stop_reason="confirmed", tool_count=2)  # fmt: skip
MCP = line("r3", seat="mcp", flow="direct", utterance="", client="Claude Desktop",
           model="external", stop_reason="validation_error", tool_count=1)  # fmt: skip
CALLS = {
    "r1": (
        RunCall("c1", "summarize_spending", {"period": {"name": "this_month"}},
                {"ok": True, "data": {"expense": {"amount": 412000}}, "meta": {"row_count": 1}},
                None),
    ),
    "r2": (
        RunCall("c1", "suggest_category", {"merchant": "김밥천국"},
                {"category_id": "food", "reason": "이력", "strategy": "history"}, None),
        RunCall("c2", "create_transaction", {"amount": 8500}, {"transaction_id": "t9"},
                datetime(2026, 10, 15, 13, 58, tzinfo=SEOUL)),
    ),
}  # fmt: skip


class Runs:
    """api 자리의 가짜 감사 로그. 받은 조건을 남긴다."""

    def __init__(self, down: bool = False) -> None:
        self.down = down
        self.asked: list[tuple[RunFilter, PageCursor | None]] = []

    async def page(self, criteria: RunFilter, cursor: PageCursor | None = None, limit: int = 30):
        if self.down:
            raise LedgerUnavailable("down")
        self.asked.append((criteria, cursor))
        lines = [r for r in (INSIGHT, CAPTURE, MCP) if criteria.seat in ("", r.seat)]
        return RunPage(tuple(lines), None if cursor else PageCursor("next"))

    async def get(self, run_id: RunId):
        if self.down:
            raise LedgerUnavailable("down")
        found = {r.id: r for r in (INSIGHT, CAPTURE, MCP)}.get(run_id)
        return RunDetail(found, CALLS.get(run_id, ())) if found else None


def browse(runs: Runs | None = None) -> tuple[TestClient, Runs]:
    runs = runs or Runs()
    app = create_app(clock=FixedClock(), seeded=False)
    app.state.services = dataclasses.replace(app.state.services, runs=runs)
    return TestClient(app), runs


def test_the_list_shows_seat_flow_status_and_what_without_any_write_button():
    browser, _ = browse()
    page = browser.get("/runs").text
    for text in ("리포트", "계획 실행", "끝남", "(assembled)", "도구 2", "2026-09"):
        assert text in page, text
    assert "외부(MCP)" in page and "Claude Desktop" in page  # MCP는 발화 대신 클라이언트
    assert "어제 점심 김밥천국 8500원" in page
    main = page.split("<main", 1)[1].lower()  # 머리의 데모 배너는 이 화면이 아니다
    assert 'method="post"' not in main and "hx-post" not in main  # 필터뿐 — 쓰기는 없다
    assert 'hx-trigger="toggle once"' in page and 'hx-target="#run-r1-calls"' in page


def test_filters_are_read_from_the_url_and_unknown_values_are_dropped():
    browser, runs = browse()
    browser.get("/runs?seat=mcp&status=bogus")
    assert runs.asked[-1][0] == RunFilter(seat="mcp", status="")


def test_changing_the_filter_swaps_the_list_and_pushes_the_url():
    browser, _ = browse()
    response = browser.get("/partials/runs?seat=capture")
    assert response.headers["HX-Push-Url"] == "/runs?seat=capture"
    assert response.text.lstrip().startswith('<section id="run-list"')


def test_more_appends_the_next_page():
    browser, runs = browse()
    assert "/partials/runs/more?cursor=next" in browser.get("/runs").text
    more = browser.get("/partials/runs/more?cursor=next").text
    assert runs.asked[-1][1] == "next" and 'id="more-runs"' not in more


def test_expanding_a_row_summarises_arguments_and_results_with_the_raw_json_folded():
    browser, _ = browse()
    calls = browser.get("/partials/runs/r1/calls").text
    assert "period=this_month" in calls and "ok · 1줄" in calls
    assert "<summary>원본</summary>" in calls and "&#34;expense&#34;" in calls
    assert "토큰 1,240" in calls and "$0.000210" in calls


def test_a_write_links_to_the_transaction_it_made_and_shows_when_it_was_confirmed():
    browser, _ = browse()
    calls = browser.get("/partials/runs/r2/calls").text
    assert 'href="/transactions/t9"' in calls and "10-15 13:58" in calls
    assert "category_id=food · reason=이력 · strategy=history" in calls


def test_one_run_on_its_own_page_and_a_missing_one_is_404():
    browser, _ = browse()
    page = browser.get("/runs/r2")
    assert (
        page.status_code == 200 and "실행 하나" in page.text and "create_transaction" in page.text
    )
    missing = browser.get("/runs/nope")
    assert missing.status_code == 404 and "그 실행을 찾지 못했어요." in missing.text


def test_an_unreachable_api_is_said_in_the_list_and_the_filters_stay():
    browser, _ = browse(Runs(down=True))
    page = browser.get("/runs")
    assert page.status_code == 200 and "가계부 서버에 닿지 못했어요" in page.text
    assert 'id="run-filters"' in page.text
    assert "도구 호출을 불러오지 못했어요." in browser.get("/partials/runs/r1/calls").text


def test_the_stand_in_shows_the_first_day_empty_state(empty_client):
    page = empty_client.get("/runs").text
    assert "아직 AI 실행이 없어요." in page


def test_header_links_to_the_runs_everywhere(client):
    for path in ("/", "/transactions"):
        assert 'href="/runs"' in client.get(path).text
