from __future__ import annotations

from tests.ui.conftest import NOW
from ui.application.dto import Direction, Source, Transaction


def tx(merchant="", memo=""):
    return Transaction(
        "t1", Direction.EXPENSE, 1_000, NOW, "food", "card", merchant, memo, Source.MANUAL
    )


def test_title_prefers_merchant_then_memo():
    assert tx(merchant="김밥천국", memo="점심").title == "김밥천국"
    assert (
        tx(memo="친구랑 점심 먹은 거 나눠 냄 영수증 없음").title
        == "친구랑 점심 먹은 거 나눠 냄 영수증"
    )
    assert tx().title == "(내역 없음)"
