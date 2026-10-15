from __future__ import annotations

from pydantic import BaseModel

from agent.application.dto import ChartPoint


class ChartPointBody(BaseModel):
    """차트의 점 하나. 값은 도구 결과에서 옮긴 것이다. 서식(원·건·일)은 화면이 unit으로 정한다."""

    label: str
    value: int | float
    annotated: bool

    @classmethod
    def of(cls, point: ChartPoint) -> ChartPointBody:
        return cls(label=point.label, value=point.value, annotated=point.annotated)
