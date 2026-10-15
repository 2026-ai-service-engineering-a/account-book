"""차트 선언을 검사하고 값을 채운다(docs/ai/agentic-reports.md 5·7장). 버리는 단위는 차트 하나다.

| kind가 bar·hbar·line인가          | 버린다. pie는 목록에 없다 |
| unit이 KRW·count·days인가         | 버린다 |
| source가 이번 실행에서 부른 id인가 | 버린다 |
| x_field·y_field가 결과의 행에 있나 | 버린다 |
| 스펙에 값 배열이 실려 왔나         | 버린다 |

값은 코드가 source의 결과를 따라가 채운다. 모델이 쓴 숫자는 그림에 들어가지 않는다.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from agent.application.dto import Chart, ChartPoint, ChartSpec, ToolStep

KINDS = ("bar", "hbar", "line")
UNITS = ("KRW", "count", "days")
MAX_ANNOTATE = 2  # 전부 달면 아무것도 읽히지 않는다


def fill_chart(spec: ChartSpec, steps: Iterable[ToolStep]) -> Chart | None:
    """통과하면 값이 채워진 차트, 하나라도 걸리면 None."""
    if spec.carried_values or spec.kind not in KINDS or spec.unit not in UNITS:
        return None
    step = next((s for s in steps if s.call.call_id == spec.source), None)
    if step is None or step.result.data is None:
        return None
    rows = _rows(step.result.data)
    points: list[ChartPoint] = []
    marks = set(spec.annotate[:MAX_ANNOTATE])
    for row in rows:
        label, value = row.get(spec.x_field), _number(row.get(spec.y_field))
        if not isinstance(label, str | int) or isinstance(label, bool) or value is None:
            return None  # 행마다 두 필드가 다 있어야 한다 — 빠진 점을 0으로 그리지 않는다
        points.append(ChartPoint(str(label), value, str(label) in marks))
    if not points:
        return None
    return Chart(spec.kind, spec.title, spec.unit, tuple(points), spec.note)


def _rows(data: Mapping[str, object]) -> list[Mapping[str, object]]:
    """결과의 행 목록 — 객체를 담은 첫 목록 칸. 합계 하나짜리 결과(summarize)에는 행이 없다."""
    for value in data.values():
        if isinstance(value, list) and value and all(isinstance(r, Mapping) for r in value):
            return [r for r in value if isinstance(r, Mapping)]
    return []


def _number(value: object) -> int | float | None:
    """금액은 {"amount", "currency"} 봉투다. 숫자 하나로 꺼낸다."""
    if isinstance(value, Mapping):
        value = value.get("amount")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return value
