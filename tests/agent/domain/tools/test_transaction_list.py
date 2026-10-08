from __future__ import annotations

from agent.domain.tools import TransactionList


def test_empty_list_is_an_answer():
    assert TransactionList((), has_more=False).transactions == ()
