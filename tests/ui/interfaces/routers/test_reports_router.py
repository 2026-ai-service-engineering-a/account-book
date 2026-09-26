from __future__ import annotations


def test_current_month_report(client):
    assert client.get("/reports", follow_redirects=False).headers["location"] == "/reports/2026-09"
    page = client.get("/reports/2026-09")
    assert page.status_code == 200
    for heading in ("어디에 썼나", "여섯 달", "카테고리별", "눈에 띈 것", "9월 17일까지"):
        assert heading in page.text
    assert "/?q=" in page.text
    assert 'aria-disabled="true">10월 →' in page.text


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
