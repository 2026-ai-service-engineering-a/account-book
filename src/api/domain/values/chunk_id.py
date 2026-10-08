from __future__ import annotations

from typing import NewType

# 조각의 식별자 — "{전략}:{법령명}/{조}/{항}[/{호}]", 고정 길이는 "{전략}:{법령명}/#{순번}".
# 경로를 품어서 사람이 읽고, 전략이 앞에 붙어 같은 항의 조각끼리 겹치지 않는다(document-rag.md 5.1).
ChunkId = NewType("ChunkId", str)
