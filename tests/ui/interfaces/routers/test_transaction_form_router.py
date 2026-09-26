from __future__ import annotations

from tests.ui.interfaces.conftest import extract

FORM = {
    "direction": "expense",
    "amount": "8,500",
    "occurred_at": "2026-09-16T12:30",
    "category_id": "food",
    "account_id": "cash",
    "merchant": "김밥천국",
    "memo": "",
    "idempotency_key": "form-1",
}


def test_new_form_defaults(empty_client):
    page = empty_client.get("/transactions/new")
    assert 'value="2026-09-17T18:00"' in page.text
    assert len(extract(r'name="idempotency_key" value="(\w+)"', page.text)) == 32


def test_submit_redirects_and_remembers_account(empty_client):
    saved = empty_client.post("/transactions", data=FORM, follow_redirects=False)
    assert saved.status_code == 303
    assert saved.headers["location"].startswith("/transactions?period=2026-09&saved=")
    assert "last_account=cash" in saved.headers["set-cookie"]
    listing = empty_client.get(saved.headers["location"])
    assert "저장했어요." in listing.text and "-8,500원" in listing.text
    assert 'value="cash" selected' in empty_client.get("/transactions/new").text


def test_resubmitting_same_key_creates_one(empty_client):
    empty_client.post("/transactions", data=FORM, follow_redirects=False)
    empty_client.post("/transactions", data=FORM, follow_redirects=False)
    page = empty_client.get("/transactions?period=2026-09")
    assert page.text.count("김밥천국") == 1


def test_htmx_submit_uses_hx_redirect(empty_client):
    saved = empty_client.post("/transactions", data=FORM, headers={"HX-Request": "true"})
    assert saved.status_code == 204 and saved.headers["HX-Redirect"].startswith("/transactions")


def test_validation_error_stays_next_to_field(empty_client):
    bad = FORM | {"amount": "-500"}
    page = empty_client.post("/transactions", data=bad, headers={"HX-Request": "true"})
    assert page.status_code == 200
    assert "금액을 숫자로 넣어 주세요." in page.text
    assert 'value="김밥천국"' in page.text  # 이미 쓴 값은 그대로
    assert "<nav>" not in page.text  # 폼 조각만


def test_api_validation_details_reach_fields(empty_client):
    bad = FORM | {"amount": "0", "category_id": "salary"}
    page = empty_client.post("/transactions", data=bad, headers={"HX-Request": "true"})
    assert "금액은 0보다 커야 합니다." in page.text
    assert "방향에 맞는 카테고리가 아닙니다." in page.text


def test_edit_and_delete(empty_client):
    location = empty_client.post("/transactions", data=FORM, follow_redirects=False).headers[
        "location"
    ]
    transaction_id = location.rsplit("saved=", 1)[1]
    edit = empty_client.get(f"/transactions/{transaction_id}")
    assert 'value="8,500"' in edit.text and "이 거래 지우기" in edit.text
    empty_client.post(f"/transactions/{transaction_id}", data=FORM | {"amount": "9000"})
    confirm = empty_client.get(f"/transactions/{transaction_id}/delete")
    assert "-9,000원 · 김밥천국" in confirm.text and "되돌릴 수 없습니다" in confirm.text
    key = extract(r'name="idempotency_key" value="(\w+)"', confirm.text)
    gone = empty_client.post(
        f"/transactions/{transaction_id}/delete",
        data={"idempotency_key": key},
        follow_redirects=False,
    )
    assert gone.status_code == 303
    assert empty_client.get(f"/transactions/{transaction_id}").status_code == 404


def test_missing_transaction_page(empty_client):
    page = empty_client.get("/transactions/t99999")
    assert page.status_code == 404 and "그 거래를 찾지 못했어요." in page.text
    assert "요청 id" in page.text


def test_category_select_follows_direction_and_suggests(empty_client):
    income = empty_client.get("/partials/category-select?direction=income&category_id=food")
    assert "급여" in income.text and "식비" not in income.text
    suggested = empty_client.get("/partials/category-select?direction=expense&merchant=스타벅스")
    assert 'value="cafe" selected' in suggested.text
    kept = empty_client.get(
        "/partials/category-select?direction=expense&merchant=스타벅스&category_id=food"
    )
    assert 'value="food" selected' in kept.text  # 사용자가 고른 것은 덮지 않는다
