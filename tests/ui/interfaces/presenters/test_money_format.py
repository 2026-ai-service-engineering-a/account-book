from __future__ import annotations

from ui.application.dto import Direction
from ui.interfaces.presenters.money_format import change, grouped, signed_won, won


def test_sign_is_text_not_color():
    assert signed_won(8_500, Direction.EXPENSE) == "-8,500원"
    assert signed_won(3_200_000, Direction.INCOME) == "+3,200,000원"
    assert signed_won(0, Direction.EXPENSE) == "0원"


def test_plain_forms():
    assert won(117_700) == "117,700원"
    assert grouped(-68_000) == "-68,000"


def test_change_shows_amount_and_percent():
    assert change(17_000, 6) == "+17,000 (6%)"
    assert change(-52_000, 57) == "-52,000 (57%)"
    assert change(5_000, None) == "+5,000"
    assert change(0, 0) == "—"
    assert change(None, None) == "—"
