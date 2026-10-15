from __future__ import annotations


def test_current_month_report(client):
    assert client.get("/reports", follow_redirects=False).headers["location"] == "/reports/2026-09"
    page = client.get("/reports/2026-09")
    assert page.status_code == 200
    for heading in ("어디에 썼나", "여섯 달", "카테고리별", "눈에 띈 것", "9월 17일까지"):
        assert heading in page.text
    assert "/?q=" in page.text  # 왜는 대화가 — AI 영역이 비어도 이 길은 남는다
    # 눈에 띈 것은 기다리지 않는다 — 페이지에는 자리만 있고 HTMX가 뒤에 채운다
    assert (
        'hx-get="/reports/2026-09/insights"' in page.text
        and '<ul class="insights">' not in page.text
    )
    assert 'aria-disabled="true">10월<svg' in page.text  # 다음 달은 이번 달까지만


def test_future_month_goes_back_to_now(client):
    moved = client.get("/reports/2027-01", follow_redirects=False)
    assert moved.headers["location"] == "/reports/2026-09"


def test_first_month_hides_comparison_and_trend(client):
    page = client.get("/reports/2026-04")
    assert "지난 달</th>" not in page.text
    assert "여섯 달" not in page.text


def test_empty_month(empty_client):
    page = empty_client.get("/reports/2026-09")
    assert "이번 달 기록이 아직 없어요." in page.text


def test_bad_period_is_404(client):
    assert client.get("/reports/september").status_code == 404


def test_the_insights_fragment_comes_after_the_page(client):
    fragment = client.get("/reports/2026-09/insights")
    assert fragment.status_code == 200 and 'id="ai-insights"' in fragment.text
    assert '<ul class="insights">' in fragment.text  # 대역의 규칙 문구


def test_no_fragment_for_an_empty_month_or_when_the_agent_is_down(client, empty_client):
    assert empty_client.get("/reports/2026-09/insights").text == ""

    async def down(period, report, budgets):
        return None

    client.app.state.services.narrator.narrate = down
    assert client.get("/reports/2026-09/insights").text == ""
    assert client.get("/reports/nope/insights").status_code == 404
