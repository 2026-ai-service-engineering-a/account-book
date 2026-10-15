from __future__ import annotations

import json

from ui.interfaces.presenters.run_view import (
    args_summary,
    pretty_json,
    result_summary,
    result_transaction,
)


def test_arguments_name_the_period_and_skip_empty_values():
    args = {"period": {"name": "this_month"}, "category_id": "food", "merchant": ""}
    assert args_summary(args) == "period=this_month · category_id=food"
    assert args_summary({"period": {"name": "last_n_days", "days": 7}}) == "period=7일"
    assert args_summary({"a": {"name": "month", "month": "2026-09"}, "b": "this_month"}) == (
        "a=2026-09 · b=this_month"
    )
    assert args_summary({}) == "인자 없음"


def test_long_summaries_are_clipped():
    summary = args_summary({"q": "가" * 200})
    assert len(summary) == 80 and summary.endswith("…")


def test_a_tool_envelope_says_ok_rows_and_why_or_the_error():
    ok = {
        "ok": True,
        "data": {},
        "meta": {"row_count": 3, "truncated": True},
        "why": "식비가 늘었다",
    }
    assert result_summary(ok) == "ok · 3줄 · 잘림 · 식비가 늘었다"
    failed = {"ok": False, "error": {"code": "validation_error", "hint": "기간 이름이 틀렸다"}}
    assert result_summary(failed) == "validation_error — 기간 이름이 틀렸다"


def test_a_small_object_lists_its_values_and_lists_by_count():
    classified = {"category_id": "food", "reason": "이력", "strategy": "history"}
    assert result_summary(classified) == "category_id=food · reason=이력 · strategy=history"
    asked = {"chunk_ids": ["a", "b"], "cited_ids": ["a"], "fell_back": False}
    assert result_summary(asked) == "chunk_ids 2개 · cited_ids 1개 · fell_back=false"


def test_no_result_and_the_transaction_a_write_made():
    assert result_summary(None) == "결과 없음"
    assert result_transaction({"transaction_id": "t9"}) == "t9"
    assert result_transaction({"ok": True}) is None and result_transaction(None) is None


def test_the_raw_json_keeps_korean_readable():
    assert json.loads(pretty_json({"merchant": "김밥천국"})) == {"merchant": "김밥천국"}
    assert "김밥천국" in pretty_json({"merchant": "김밥천국"})
