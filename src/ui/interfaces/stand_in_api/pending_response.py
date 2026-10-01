from __future__ import annotations

from pydantic import BaseModel

from .pending_body import PendingBody


class PendingResponse(BaseModel):
    items: list[PendingBody]
