from __future__ import annotations

from datetime import datetime

from tests.ui.conftest import NOW, SEOUL
from ui.application.dto import Direction, MessageReading
from ui.interfaces.forms.transaction_form import TransactionForm


def test_blank_has_defaults_and_key():
    form = TransactionForm.blank(NOW, "cash")
    assert (form.direction, form.occurred_at, form.account_id) == (
        "expense",
        "2026-09-17T18:00",
        "cash",
    )
    assert len(form.idempotency_key) == 32


def test_parse_accepts_grouped_amount():
    form = TransactionForm(amount="8,500원", occurred_at="2026-09-16T12:30", category_id="food")
    draft, errors = form.parse(SEOUL)
    assert errors == {}
    assert draft is not None and draft.amount == 8_500
    assert draft.occurred_at == datetime(2026, 9, 16, 12, 30, tzinfo=SEOUL)


def test_parse_reports_each_bad_field():
    draft, errors = TransactionForm(amount="팔천", occurred_at="어제").parse(SEOUL)
    assert draft is None
    assert set(errors) == {"amount", "occurred_at", "category_id"}


def test_from_mapping_ignores_non_text_and_unknown():
    form = TransactionForm.from_mapping(
        {"direction": "income", "amount": " 10 ", "x": "y", "memo": object()}
    )
    assert form.direction_value == Direction.INCOME
    assert (form.amount, form.memo) == ("10", "")


def test_applies_only_what_was_read():
    form = TransactionForm(merchant="원래 가게", account_id="cash")
    filled = form.apply(
        MessageReading(
            direction=Direction.INCOME,
            amount=3_200_000,
            occurred_at=datetime(2026, 9, 10, 9, 0, tzinfo=SEOUL),
        ),
        SEOUL,
    )
    assert filled == {"amount", "direction", "occurred_at"}
    assert (form.amount, form.direction, form.occurred_at) == (
        "3,200,000",
        "income",
        "2026-09-10T09:00",
    )
    assert (form.merchant, form.account_id) == ("원래 가게", "cash")


def test_refusal_or_missing_amount_changes_nothing():
    form = TransactionForm(amount="1,000")
    assert form.apply(MessageReading(refusal="못 읽음"), SEOUL) == frozenset()
    assert form.apply(MessageReading(merchant="가게"), SEOUL) == frozenset()
    assert (form.amount, form.merchant) == ("1,000", "")
