from __future__ import annotations

from dataclasses import dataclass

from ui.application.values import CategoryId

from .direction import Direction


@dataclass(frozen=True, slots=True)
class Category:
    id: CategoryId
    name: str
    direction: Direction
