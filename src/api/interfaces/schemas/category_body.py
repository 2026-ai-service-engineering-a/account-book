from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from api.domain.entities import Category


class CategoryBody(BaseModel):
    id: str
    name: str
    direction: Literal["expense", "income"]

    @classmethod
    def of(cls, category: Category) -> CategoryBody:
        return cls(id=category.id, name=category.name, direction=category.direction.value)
