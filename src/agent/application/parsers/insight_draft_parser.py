"""조립 호출(LLM 2)이 낸 JSON을 `InsightDraft`로. `Any`(모양을 모르는 값)는 여기서 끝난다.

글 칸이 글이 아니면 전체가 `MalformedOutput`이다(한 번 다시 시킨다). 값 배열이 실려 왔는지는
표시만 해 둔다 — 그 차트를 버리는 것은 검사(chart_fill)의 일이다(agentic-reports 7장).
"""

from __future__ import annotations

from collections.abc import Mapping

from agent.application.dto import ChartSpec, HighlightDraft, InsightDraft
from agent.application.errors import MalformedOutput

# 스펙에 값이 실려 왔다는 표시 — 스펙에는 source와 필드 이름만 있어야 한다
_VALUE_KEYS = {"data", "values", "points", "series", "rows"}
_TEXT_KEYS = ("kind", "title", "source", "x_field", "y_field", "unit")
_TEXT_LIMIT = 200


def parse_insight_draft(raw: Mapping[str, object]) -> InsightDraft:
    charts, highlights = raw.get("charts"), raw.get("highlights")
    if not isinstance(charts, list) or not isinstance(highlights, list):
        raise MalformedOutput("charts와 highlights는 목록이다")
    return InsightDraft(tuple(_chart(c) for c in charts), tuple(_highlight(h) for h in highlights))


def _chart(raw: object) -> ChartSpec:
    if not isinstance(raw, Mapping):
        raise MalformedOutput("차트가 객체가 아니다")
    texts = {key: raw.get(key) for key in _TEXT_KEYS}
    if not all(isinstance(v, str) for v in texts.values()):
        raise MalformedOutput("차트의 kind·title·source·x_field·y_field·unit은 글이다")
    annotate, note = raw.get("annotate", []), raw.get("note", "")
    if not isinstance(annotate, list) or not all(isinstance(a, str) for a in annotate):
        raise MalformedOutput("annotate는 글의 목록이다")
    if not isinstance(note, str):
        raise MalformedOutput("note는 글이다")
    return ChartSpec(
        kind=str(texts["kind"]).strip(),
        title=str(texts["title"]).strip()[:_TEXT_LIMIT],
        source=str(texts["source"]).strip(),
        x_field=str(texts["x_field"]).strip(),
        y_field=str(texts["y_field"]).strip(),
        unit=str(texts["unit"]).strip(),
        annotate=tuple(a.strip() for a in annotate),
        note=note.strip()[:_TEXT_LIMIT],
        carried_values=bool(_VALUE_KEYS & set(raw)),
    )


def _highlight(raw: object) -> HighlightDraft:
    if not isinstance(raw, Mapping):
        raise MalformedOutput("문장이 객체가 아니다")
    text, source = raw.get("text"), raw.get("source", "")
    if not isinstance(text, str) or not isinstance(source, str):
        raise MalformedOutput("문장의 text·source는 글이다")
    return HighlightDraft(text.strip()[:_TEXT_LIMIT], source.strip())
