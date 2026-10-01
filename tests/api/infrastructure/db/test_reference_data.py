from __future__ import annotations

from api.infrastructure.db.reference_data import ACCOUNTS, CATEGORIES


def test_same_ids_as_the_ui_stand_in():
    # 거래가 api로 옮겨 와도 화면·에이전트·평가 세트가 같은 id를 쓴다
    assert {c[0] for c in CATEGORIES} == {
        "food",
        "cafe",
        "transport",
        "living",
        "housing",
        "etc",
        "salary",
        "other_income",
    }
    assert {a[0] for a in ACCOUNTS} == {"card", "cash", "bank"}


def test_every_category_has_a_direction():
    assert {c[2] for c in CATEGORIES} == {"expense", "income"}
