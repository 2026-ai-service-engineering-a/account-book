from __future__ import annotations

from agent.application.errors import InvalidToolArguments, MalformedOutput


def test_names_the_field_for_the_model():
    error = InvalidToolArguments("period", "기간 이름이 아니다")
    assert (error.field, error.hint) == ("period", "기간 이름이 아니다")
    assert not isinstance(error, MalformedOutput)  # 다시 시키는 게 아니라 봉투로 돌려준다
