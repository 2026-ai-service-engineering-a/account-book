from __future__ import annotations

import dataclasses

from fastapi.testclient import TestClient

from tests.ui.conftest import FixedClock
from tests.ui.interfaces.conftest import extract
from ui.interfaces.routers.transaction_form_router import SAMPLE_CARD_MESSAGE, SAMPLE_SENTENCE
from ui.main import create_app

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
    assert 'id="site-header"' in page.text  # 페이지는 머리까지, 조각은 머리 없이
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
    assert 'id="site-header"' not in page.text  # 폼 조각만


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


# ── 한 줄로 채우기(transaction-form.md 4.4) ──

READ = "/partials/transaction-form/read"
HX = {"HX-Request": "true"}
BLANK = {
    "direction": "expense",
    "amount": "",
    "occurred_at": "2026-09-17T18:00",
    "category_id": "",
    "account_id": "cash",
    "merchant": "",
    "memo": "회식",
    "idempotency_key": "form-1",
}


def test_new_form_offers_the_box_and_edit_form_does_not(empty_client):
    page = empty_client.get("/transactions/new")
    assert "한 줄로 채우기" in page.text and "카드 문자</button>" in page.text
    empty_client.post("/transactions", data=BLANK | {"amount": "1000", "category_id": "food"})
    listing = empty_client.get("/transactions?period=2026-09").text
    transaction_id = listing.split('href="/transactions/t', 1)[1].split('"', 1)[0]
    assert "한 줄로 채우기" not in empty_client.get(f"/transactions/t{transaction_id}").text


def test_sample_message_fills_and_marks_fields(empty_client):
    page = empty_client.post(READ, data=BLANK | {"capture_text": SAMPLE_CARD_MESSAGE}, headers=HX)
    assert page.status_code == 200 and 'id="site-header"' not in page.text
    for value in ('value="8,500"', 'value="2026-09-16T12:31"', 'value="김밥천국"'):
        assert value in page.text
    assert 'value="food" selected' in page.text  # 카테고리는 제안이 이어서 채운다
    assert 'value="card" selected' in page.text
    assert page.text.count("AI가 채움") == 6
    assert "확인하고 저장하세요" in page.text
    assert 'value="form-1"' in page.text  # 멱등성 키는 화면을 열 때 것 그대로
    assert 'value="회식"' in page.text  # 읽지 않은 칸은 그대로


def test_unread_fields_keep_user_values_and_are_listed(empty_client):
    data = BLANK | {"merchant": "스벅", "capture_text": "현대카드 승인 5,800원"}
    page = empty_client.post(READ, data=data, headers=HX)
    assert 'value="5,800"' in page.text and 'value="스벅"' in page.text
    assert "읽지 못한 칸: 날짜, 가맹점" in page.text


def test_user_chosen_category_is_not_overwritten(empty_client):
    data = BLANK | {"category_id": "etc", "capture_text": SAMPLE_CARD_MESSAGE}
    page = empty_client.post(READ, data=data, headers=HX)
    assert 'value="etc" selected' in page.text
    assert page.text.count("AI가 채움") == 5


def test_refusal_changes_nothing(empty_client):
    data = BLANK | {
        "amount": "1,000",
        "capture_text": "신한카드 승인취소 8,500원 09/16 12:31 김밥천국",
    }
    page = empty_client.post(READ, data=data, headers=HX)
    assert 'value="1,000"' in page.text
    assert "승인 취소 문자는 아직 읽지 않아요" in page.text
    assert "AI가 채움" not in page.text


def test_blank_paste(empty_client):
    page = empty_client.post(READ, data=BLANK | {"capture_text": "  "}, headers=HX)
    assert "보낸 내용이 없어요." in page.text


def test_filled_form_still_saves_through_the_normal_path(empty_client):
    page = empty_client.post(READ, data=BLANK | {"capture_text": SAMPLE_CARD_MESSAGE}, headers=HX)
    assert "AI가 채움" in page.text
    data = BLANK | {
        "amount": "8,500",
        "occurred_at": "2026-09-16T12:31",
        "category_id": "food",
        "account_id": "card",
        "merchant": "김밥천국",
        "capture_text": SAMPLE_CARD_MESSAGE,
    }
    saved = empty_client.post("/transactions", data=data, follow_redirects=False)
    assert saved.status_code == 303
    listing = empty_client.get(saved.headers["location"]).text
    assert "김밥천국" in listing and "누적" not in listing  # 원문은 어디에도 남지 않는다


def test_without_ai_the_box_disappears_and_form_still_works():
    app = create_app(clock=FixedClock(), seeded=False, token_delay=0, capture_delay=0)
    app.state.services = dataclasses.replace(app.state.services, capture=None)
    client = TestClient(app)
    assert "한 줄로 채우기" not in client.get("/transactions/new").text
    assert client.post(READ, data=BLANK | {"capture_text": SAMPLE_CARD_MESSAGE}).status_code == 404
    saved = client.post(
        "/transactions",
        data=BLANK | {"amount": "1000", "category_id": "food"},
        follow_redirects=False,
    )
    assert saved.status_code == 303


def test_sentence_fills_like_a_chat(empty_client):
    page = empty_client.post(READ, data=BLANK | {"capture_text": SAMPLE_SENTENCE}, headers=HX)
    for value in ('value="5,000"', 'value="2026-09-17T15:00"', 'value="카페"'):
        assert value in page.text
    assert 'value="cafe" selected' in page.text
    assert 'value="cash" selected' in page.text  # 결제수단을 말하지 않았으니 그대로
    assert '<div class="bubble me">오늘 오후 3시에 카페에서 5천원 썼어</div>' in page.text
    assert "확인하고 저장하세요" in page.text
    assert (
        'name="capture_text"' in page.text and "5천원 썼어</textarea>" not in page.text
    )  # 입력칸은 비운다


def test_question_is_sent_to_chat(empty_client):
    page = empty_client.post(
        READ, data=BLANK | {"capture_text": "이번 달 식비 얼마 썼어?"}, headers=HX
    )
    assert "질문은 채팅에서 물어 주세요" in page.text
    assert "AI가 채움" not in page.text
