from __future__ import annotations

from ui.application.values import ProposalId


def test_is_plain_text_at_runtime():
    # NewType은 타입 검사기에만 있다. 템플릿·URL로 나갈 때 그대로 글자다.
    value = ProposalId("9f2c")
    assert value == "9f2c" and isinstance(value, str)
