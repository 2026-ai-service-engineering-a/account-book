from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId, Confidence


@dataclass(frozen=True, slots=True)
class Candidate:
    category_id: CategoryId
    confidence: Confidence
