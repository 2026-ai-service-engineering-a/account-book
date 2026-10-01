from __future__ import annotations

from pydantic import BaseModel


class CategoryBody(BaseModel):
    id: str
    name: str
