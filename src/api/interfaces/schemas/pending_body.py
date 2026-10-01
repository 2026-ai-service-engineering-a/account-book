from __future__ import annotations

from pydantic import BaseModel


class PendingBody(BaseModel):
    text_hash: str
    text: str
