from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import CategoryId, Direction


@dataclass(frozen=True, slots=True)
class Category:
    id: CategoryId
    name: str
    direction: Direction
