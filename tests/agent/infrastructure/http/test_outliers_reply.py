from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.infrastructure.http.outliers_reply import OutliersReply


def test_an_empty_answer_is_still_a_report():
    reply = OutliersReply.model_validate(
        {
            "baseline_from": "2026-03-01T00:00:00+09:00",
            "baseline_to": "2026-09-01T00:00:00+09:00",
            "items": [],
            "truncated": False,
            "skipped": [],
        }
    )
    assert reply.report().items == () and reply.report().skipped == ()


def test_a_naive_baseline_is_an_unknown_shape():
    with pytest.raises(ValidationError):
        OutliersReply.model_validate(
            {
                "baseline_from": "2026-03-01T00:00:00",
                "baseline_to": "2026-09-01T00:00:00",
                "items": [],
                "truncated": False,
                "skipped": [],
            }
        )
