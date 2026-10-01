from __future__ import annotations

from pydantic import BaseModel


class CandidateBody(BaseModel):
    category_id: str
    confidence: float
