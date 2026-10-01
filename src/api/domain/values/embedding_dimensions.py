from __future__ import annotations

# 벡터의 차원. agent의 EMBEDDING_DIMENSIONS와 같아야 한다. pgvector의 HNSW 인덱스는 차원이 정해진
# 열에만 걸리고 2000차원까지 받는다 — 그래서 768이다(docs/ai/category-suggestion-rag.md 5장).
# 바꾸려면 마이그레이션이 필요하다.
EMBEDDING_DIMENSIONS = 768
