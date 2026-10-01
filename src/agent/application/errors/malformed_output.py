from __future__ import annotations


class MalformedOutput(Exception):
    """LLM의 답이 스키마를 못 맞췄다. 한 번 다시 시키고, 또 틀리면 버린다(docs/ai 원칙 3)."""
