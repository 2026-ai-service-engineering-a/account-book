from __future__ import annotations

from api.domain.errors import ConfirmationRequired, InvalidTransaction


def test_is_not_a_validation_error():
    # 고칠 값이 없다 — 사람이 확인하고 같은 키로 다시 보내면 된다
    assert not issubclass(ConfirmationRequired, InvalidTransaction)
