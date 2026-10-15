"""리포트 AI 영역을 캐시에 넣을 JSON으로, 그리고 되돌리기. 담는 것은 화면에 갈 것뿐이다 —
도구 결과와 계획은 감사 로그의 몫이다."""

from __future__ import annotations

from collections.abc import Mapping

from agent.application.dto import Chart, ChartPoint, Insight, InsightStop


def insight_body(insight: Insight) -> dict[str, object]:
    return {
        "charts": [
            {
                "kind": c.kind,
                "title": c.title,
                "unit": c.unit,
                "note": c.note,
                "points": [[p.label, p.value, p.annotated] for p in c.points],
            }
            for c in insight.charts
        ],
        "highlights": list(insight.highlights),
    }


def insight_from_body(body: Mapping[str, object]) -> Insight | None:
    """모양이 틀리면 None — 캐시를 못 믿으면 새로 만든다. 예외로 리포트를 막지 않는다."""
    charts, highlights = body.get("charts"), body.get("highlights")
    if not isinstance(charts, list) or not isinstance(highlights, list):
        return None
    if not all(isinstance(h, str) for h in highlights):
        return None
    try:
        drawn = tuple(_chart(c) for c in charts)
    except (KeyError, TypeError, ValueError):
        return None
    return Insight(InsightStop.CACHED, drawn, tuple(str(h) for h in highlights))


def _chart(raw: object) -> Chart:
    if not isinstance(raw, Mapping):
        raise TypeError("차트가 객체가 아니다")
    points = []
    for label, value, annotated in raw["points"]:
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise TypeError("값이 숫자가 아니다")
        points.append(ChartPoint(str(label), value, bool(annotated)))
    return Chart(
        str(raw["kind"]), str(raw["title"]), str(raw["unit"]), tuple(points), str(raw["note"])
    )
