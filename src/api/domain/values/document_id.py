from __future__ import annotations

from typing import NewType

# 문서의 식별자 — 법령명이다(docs/ai/document-rag.md 5.1). "조세특례제한법"
DocumentId = NewType("DocumentId", str)
