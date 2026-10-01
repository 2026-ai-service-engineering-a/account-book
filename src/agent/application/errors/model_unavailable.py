from __future__ import annotations


class ModelUnavailable(Exception):
    """LLM 제공자에 닿지 못했다 — 키, 네트워크, 타임아웃, 한도. 다시 시켜도 같은 답이 온다."""
