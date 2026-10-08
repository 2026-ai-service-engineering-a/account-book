from __future__ import annotations

from agent.domain.values import PeriodName


def test_the_names_the_model_may_pick():
    assert {n.value for n in PeriodName} == {
        "today",
        "yesterday",
        "this_week",
        "last_week",
        "this_month",
        "last_month",
        "this_year",
        "last_n_days",
        "month",
        "range",
    }
