"""실행 기록 화면의 이름과 요약(ui_docs/pages/runs.md 3장).

감사 로그는 저장된 JSON 그대로 온다. 자리마다 모양이 달라 여기서 넷으로 가른다 — 도구 봉투,
작은 객체, 거래 id, 없음. 요약은 무엇을 물었고 무엇이 돌아왔나까지만 말한다. 다 보려면 원본을 연다.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

SEATS = {
    "capture": "기록",
    "classify": "카테고리 고르기",
    "chat": "대화 통계",
    "ask": "문서 Q&A",
    "insight": "리포트",
    "mcp": "외부(MCP)",
}
FLOWS = {"single": "단발", "react": "ReAct", "plan_execute": "계획 실행", "direct": "직접"}
STATUSES = {
    "done": "끝남",
    "failed": "실패",
    "awaiting_confirmation": "확인 대기",
    "aborted": "취소됨",
}
_LIMIT = 80  # 요약의 길이. 넘으면 자르고 …을 붙인다
_PERIOD_KEYS = {"period", "a", "b"}


def args_summary(args: Mapping[str, object]) -> str:
    """맨 위 칸을 `키=값`으로 잇는다. 기간은 이름만, 그 밖의 객체는 한 줄 JSON."""
    parts = [
        f"{key}={_period(value) if key in _PERIOD_KEYS else _value(value)}"
        for key, value in args.items()
        if value not in (None, "", [], {})
    ]
    return _clip(" · ".join(parts)) or "인자 없음"


def result_summary(result: Mapping[str, object] | None) -> str:
    if result is None:
        return "결과 없음"
    if isinstance(result.get("ok"), bool):
        return _clip(_envelope(result))
    parts = []
    for key, value in result.items():
        if isinstance(value, list):
            parts.append(f"{key} {len(value)}개")
        elif isinstance(value, str | int | float | bool) or value is None:
            parts.append(f"{key}={_value(value)}")
    return _clip(" · ".join(parts)) or "결과 있음"


def result_transaction(result: Mapping[str, object] | None) -> str | None:
    """쓰기가 만든 거래 — 결과에 있으면 그 거래로 잇는다."""
    found = result.get("transaction_id") if result is not None else None
    return found if isinstance(found, str) and found else None


def pretty_json(value: object) -> str:
    """원본 — 펼침 안의 펼침에 그대로."""
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False)


def _envelope(result: Mapping[str, object]) -> str:
    """도구 봉투 `{ok, data|error, meta}`(docs/ai/tools.md 3장)."""
    if result["ok"] is not True:
        error = result.get("error")
        error = error if isinstance(error, Mapping) else {}
        return f"{error.get('code', '실패')} — {error.get('hint', '')}".rstrip(" —")
    meta = result.get("meta")
    meta = meta if isinstance(meta, Mapping) else {}
    parts = ["ok"]
    if isinstance(meta.get("row_count"), int):
        parts.append(f"{meta['row_count']}줄")
    if meta.get("truncated") is True:
        parts.append("잘림")
    why = result.get("why")
    if isinstance(why, str) and why:
        parts.append(why)  # 리포트의 계획이 이 집계를 고른 이유
    return " · ".join(parts)


def _period(value: object) -> str:
    if not isinstance(value, Mapping):
        return _value(value)
    name = value.get("name")
    if name == "last_n_days":
        return f"{value.get('days')}일"
    if name == "month" and value.get("month"):
        return str(value["month"])
    if name == "range":
        return f"{value.get('start')}~{value.get('end')}"
    return str(name) if name else _value(value)


def _value(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _clip(text: str) -> str:
    return text if len(text) <= _LIMIT else text[: _LIMIT - 1] + "…"
