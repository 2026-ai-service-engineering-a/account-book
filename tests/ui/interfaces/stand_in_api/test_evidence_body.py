from __future__ import annotations

import pytest
from pydantic import ValidationError

from ui.interfaces.stand_in_api import EvidenceBody


def test_time_must_be_aware():
    with pytest.raises(ValidationError):
        EvidenceBody(
            transaction_id="t1",
            merchant="m",
            memo="",
            category_id="cafe",
            amount=1,
            occurred_at="2026-09-01T12:00:00",
            similarity=None,
        )
