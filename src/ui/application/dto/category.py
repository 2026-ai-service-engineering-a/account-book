from __future__ import annotations

from dataclasses import dataclass

from .direction import Direction


@dataclass(frozen=True, slots=True)
class Category:
    id: str
    name: str
    direction: Direction
