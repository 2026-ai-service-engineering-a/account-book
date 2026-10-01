from __future__ import annotations

from typing import NewType

# 카테고리의 식별자. 목록은 api가 갖는다 — LLM이 새로 만들지 못한다.
CategoryId = NewType("CategoryId", str)
