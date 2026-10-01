from __future__ import annotations

import dataclasses

from fastapi.testclient import TestClient

from tests.ui.conftest import FixedClock
from tests.ui.interfaces.conftest import FixedSuggester
from ui.application.dto import CategorySuggestion
from ui.application.values import CategoryId
from ui.main import create_app


def test_category_select_follows_direction_without_choosing(empty_client):
    income = empty_client.get("/partials/category-select?direction=income&category_id=food")
    assert "급여" in income.text and "식비" not in income.text
    assert 'value="" selected' in income.text  # 방향에 안 맞는 카테고리는 비운다
    kept = empty_client.get("/partials/category-select?direction=expense&category_id=food")
    assert 'value="food" selected' in kept.text


def test_merchant_field_no_longer_suggests_on_its_own(empty_client):
    # 누르기 전에는 아무것도 부르지 않는다(category-suggestion-rag 8.1)
    page = empty_client.get("/transactions/new").text
    merchant = page[page.index('id="merchant"') :].split(">", 1)[0]
    assert "hx-get" not in merchant
    assert "AI로 고르기" in page


SUGGEST = "/partials/category-suggest"


def test_ai_button_fills_and_shows_why(empty_client):
    form = {"direction": "expense", "merchant": "스타벅스", "memo": "", "category_id": ""}
    page = empty_client.post(SUGGEST, data=form).text
    assert 'value="cafe" selected' in page and "AI가 채움" in page
    assert "각본 대역: &#39;스타벅스&#39; 낱말" in page or "각본 대역: '스타벅스' 낱말" in page


def test_ai_button_overwrites_because_pressing_it_is_consent(empty_client):
    form = {"direction": "expense", "merchant": "스타벅스", "category_id": "food"}
    assert 'value="cafe" selected' in empty_client.post(SUGGEST, data=form).text


def test_ai_button_that_cannot_choose_leaves_the_select_alone(empty_client):
    form = {"direction": "expense", "merchant": "처음 보는 가게", "category_id": "food"}
    page = empty_client.post(SUGGEST, data=form).text
    assert 'value="food" selected' in page and "AI가 채움" not in page
    assert "직접 골라 주세요" in page


def test_llm_choice_is_marked_ai():
    app = create_app(clock=FixedClock(), seeded=False, token_delay=0, capture_delay=0)
    chosen = CategorySuggestion(CategoryId("food"), "배달앱 기록을 보고 골랐어요.", by_llm=True)
    app.state.services = dataclasses.replace(app.state.services, suggester=FixedSuggester(chosen))
    page = TestClient(app).post(SUGGEST, data={"direction": "expense", "merchant": "쿠팡이츠"}).text
    assert '<span class="ai-tag">AI</span> 배달앱 기록을 보고 골랐어요.' in page
