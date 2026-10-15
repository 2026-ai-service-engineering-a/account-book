from __future__ import annotations

from api.application.use_cases import ReadDataVersion
from tests.api.application.use_cases.test_detect_outliers import OCTOBER, ledger, spend


def test_the_same_data_is_the_same_version_and_a_change_moves_it():
    uow = ledger()
    before = ReadDataVersion(uow)(OCTOBER)
    assert ReadDataVersion(uow)(OCTOBER) == before
    uow.transactions.add(spend(99, "food", 12000, 10, 20))
    assert ReadDataVersion(uow)(OCTOBER) != before
