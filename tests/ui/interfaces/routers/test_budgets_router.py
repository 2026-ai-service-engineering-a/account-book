from __future__ import annotations


def test_budget_page_lists_every_expense_category(client):
    page = client.get("/budgets")
    for name in ("식비", "카페", "교통", "생활"):
        assert name in page.text
    assert "정하지 않음" in page.text  # 카페


def test_empty_budgets_hint(empty_client):
    assert "많이 쓰는 카테고리부터 정해보세요." in empty_client.get("/budgets").text


def test_row_edit_save_and_cancel(empty_client):
    edit = empty_client.get("/budgets/cafe/edit")
    assert 'hx-put="/budgets/cafe"' in edit.text
    saved = empty_client.put("/budgets/cafe", data={"amount": "50,000", "idempotency_key": "b"})
    assert 'id="budget-row-cafe"' in saved.text and "50,000" in saved.text
    cancel = empty_client.get("/budgets/cafe")
    assert "50,000" in cancel.text and "hx-put" not in cancel.text


def test_bad_amount_stays_in_the_row(empty_client):
    row = empty_client.put("/budgets/food", data={"amount": "abc", "idempotency_key": "b"})
    assert "숫자로 넣어 주세요" in row.text and 'value="abc"' in row.text
    zero = empty_client.put("/budgets/food", data={"amount": "0", "idempotency_key": "b"})
    assert "예산은 0보다 커야 합니다." in zero.text


def test_blank_amount_clears_budget(client):
    row = client.put("/budgets/food", data={"amount": "", "idempotency_key": "b"})
    assert "정하지 않음" in row.text
