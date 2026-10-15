from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChartSpec:
    """모델이 낸 차트 선언(ai/agentic-reports.md 5장). 값은 없다 — `source`와 필드 이름뿐이다.

    `carried_values`는 스펙에 값 배열이 실려 왔다는 표시다. 그런 스펙은 버린다 — 지어낸 숫자인지
    확인할 방법이 없다.
    """

    kind: str
    title: str
    source: str  # 이번 실행에서 부른 도구의 call_id
    x_field: str
    y_field: str
    unit: str
    annotate: tuple[str, ...] = ()
    note: str = ""
    carried_values: bool = False
