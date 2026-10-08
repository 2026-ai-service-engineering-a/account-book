"""읽기 도구 여섯의 설명과 입력 JSON Schema. 모델이 읽는 문서다(ai/tools.md 2장).

이 파일이 바뀌면 모델에게 주는 프롬프트가 바뀐 것이다 — 모드별 스키마 스냅샷 테스트가
리뷰에서 그 차이를 보이게 한다(ai/tools.md 8장).
"""

from __future__ import annotations

from collections.abc import Mapping

from agent.domain.values import Direction, PeriodName

from .search_transactions_input import DEFAULT_ROWS, MAX_ROWS
from .tool_name import ToolName
from .tool_spec import ToolSpec

_PERIOD: Mapping[str, object] = {
    "type": "object",
    "description": (
        "기간은 이름만 고른다. 날짜를 계산하지 않는다. 최근 n일은 days, 특정 달은 month(YYYY-MM), "
        "질문에 날짜가 적혔을 때만 range로 start·end(YYYY-MM-DD, 끝 날짜 포함)를 그대로 옮긴다."
    ),
    "properties": {
        "name": {"type": "string", "enum": [n.value for n in PeriodName]},
        "days": {"type": "integer", "minimum": 1, "maximum": 365},
        "month": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
        "start": {"type": "string", "format": "date"},
        "end": {"type": "string", "format": "date"},
    },
    "required": ["name"],
    "additionalProperties": False,
}
_CATEGORY: Mapping[str, object] = {
    "type": "string",
    "description": "카테고리 사전에 있는 id만. 사전에 없으면 비우고 merchant로 찾는다.",
}
_MERCHANT: Mapping[str, object] = {
    "type": "string",
    "description": "가맹점·메모에 든 글자(부분 일치).",
}
_DIRECTION: Mapping[str, object] = {"type": "string", "enum": [d.value for d in Direction]}


def _object(properties: Mapping[str, object], required: list[str]) -> Mapping[str, object]:
    return {
        "type": "object",
        "properties": dict(properties),
        "required": required,
        "additionalProperties": False,
    }


READ_TOOLS: Mapping[ToolName, ToolSpec] = {
    spec.name: spec
    for spec in (
        ToolSpec(
            ToolName.SEARCH_TRANSACTIONS,
            does=f"기간 안의 거래를 최근 것부터 한 줄씩 보여준다"
            f"(기본 {DEFAULT_ROWS}건, 최대 {MAX_ROWS}건).",
            avoid="합계·건수·비교를 세려고 쓰지 않는다 — summarize_spending·count_frequency·"
            "compare_periods를 쓴다.",
            input_schema=_object(
                {
                    "period": _PERIOD,
                    "category_id": _CATEGORY,
                    "merchant": _MERCHANT,
                    "direction": _DIRECTION,
                    "limit": {"type": "integer", "minimum": 1, "maximum": MAX_ROWS},
                },
                ["period"],
            ),
        ),
        ToolSpec(
            ToolName.SUMMARIZE_SPENDING,
            does="기간 안의 지출 합과 수입 합을 낸다. 카테고리·가맹점으로 좁힐 수 있다.",
            avoid="몇 번인지는 count_frequency, 두 기간을 견주는 건 compare_periods를 쓴다.",
            input_schema=_object(
                {
                    "period": _PERIOD,
                    "category_id": _CATEGORY,
                    "merchant": _MERCHANT,
                    "direction": _DIRECTION,
                },
                ["period"],
            ),
        ),
        ToolSpec(
            ToolName.COUNT_FREQUENCY,
            does="기간 안의 거래 건수와 거래가 있던 날 수, 날 사이 평균 간격, 회당 평균을 센다.",
            avoid="금액 합계가 필요하면 이 도구가 아니라 summarize_spending을 쓴다.",
            input_schema=_object(
                {
                    "period": _PERIOD,
                    "category_id": _CATEGORY,
                    "merchant": _MERCHANT,
                    "direction": _DIRECTION,
                },
                ["period"],
            ),
        ),
        ToolSpec(
            ToolName.COMPARE_PERIODS,
            does="두 기간의 지출을 카테고리별로 견주어 합과 증감(b - a, 금액·비율)을 낸다.",
            avoid="한 기간의 합만 필요하면 summarize_spending을 쓴다.",
            input_schema=_object(
                {"a": _PERIOD, "b": _PERIOD, "category_id": _CATEGORY}, ["a", "b"]
            ),
        ),
        ToolSpec(
            ToolName.GET_BUDGET_STATUS,
            does="한 달의 카테고리별 예산·쓴 돈·남은 돈·소진율·말일 예상을 낸다.",
            avoid="예산은 달 단위다. 주·일 기간이나 예산과 상관없는 지출 합에는 쓰지 않는다.",
            input_schema=_object({"period": _PERIOD, "category_id": _CATEGORY}, ["period"]),
        ),
        ToolSpec(
            ToolName.SUGGEST_CATEGORY,
            does="가맹점·메모로 카테고리 후보와 근거 거래, 그 방향의 카테고리 사전을 낸다.",
            avoid="이미 기록된 거래를 찾거나 세는 데는 쓰지 않는다 — "
            "새 기록의 카테고리를 고를 때만.",
            input_schema=_object(
                {
                    "merchant": {"type": "string"},
                    "memo": {"type": "string"},
                    "direction": _DIRECTION,
                },
                ["merchant"],
            ),
        ),
    )
}
