from __future__ import annotations


def test_first_day_empty_state(empty_client):
    page = empty_client.get("/transactions")
    assert "아직 기록이 없어요" in page.text
    assert "필터를 지워볼까요" not in page.text


def test_filter_miss_has_different_words(client):
    page = client.get("/transactions?q=없는가게")
    assert "조건에 맞는 거래가 없어요" in page.text


def test_list_shows_signs_and_separate_totals(client):
    page = client.get("/transactions?period=2026-09")
    assert "지출 합" in page.text and "수입 합" in page.text
    assert "+3,200,000원" in page.text  # 9월 급여
    assert "-450,000원" in page.text  # 월세


def test_partial_swaps_summary_out_of_band_and_pushes_url(client):
    part = client.get(
        "/partials/transactions?period=2026-09&direction=expense&category=food",
        headers={"HX-Request": "true"},
    )
    assert 'id="summary" hx-swap-oob="true"' in part.text
    assert 'id="transaction-list"' in part.text
    assert part.headers["HX-Push-Url"] == (
        "/transactions?period=2026-09&direction=expense&category=food"
    )
    assert "+3,200,000원" not in part.text


def test_more_button_pages_with_cursor(client):
    page = client.get("/transactions?period=2026-08")
    assert 'id="more-row"' in page.text
    more = client.get("/partials/transactions/more?period=2026-08&cursor=50")
    assert "<tr>" in more.text


def test_bad_filter_values_fall_back(client):
    assert client.get("/transactions?period=nope&direction=sideways").status_code == 200
