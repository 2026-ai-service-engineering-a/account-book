"""금액을 화면 글자로. 부호는 글자로 붙인다 — 색으로만 구분하지 않는다(ui-design 2.1)."""

from __future__ import annotations

from ui.application.dto import Direction


def won(amount: int) -> str:
    return f"{amount:,}원"


def signed_won(amount: int, direction: Direction) -> str:
    if amount == 0:
        return "0원"
    sign = "+" if direction == Direction.INCOME else "-"
    return f"{sign}{amount:,}원"


def grouped(amount: int) -> str:
    return f"{amount:,}"


def change(delta: int | None, percent: int | None) -> str:
    """증감은 금액과 퍼센트를 같이 낸다. 1,000원이 2,000원이 된 것도 100%다."""
    if not delta:
        return "—"
    text = f"{delta:+,}"
    return f"{text} ({percent}%)" if percent is not None else text
