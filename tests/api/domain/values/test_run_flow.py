from __future__ import annotations

from api.domain.values import RunFlow


def test_same_values_as_the_check_constraint():
    assert {f.value for f in RunFlow} == {"single", "react", "plan_execute"}
