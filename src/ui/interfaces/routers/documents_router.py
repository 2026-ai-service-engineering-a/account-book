"""문서 화면 — 법령 조각을 찾아 원문을 인용으로 보인다(ui_docs/pages/documents.md)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from ui.application.dto import ChunkStrategy
from ui.interfaces.services import ServicesDep
from ui.interfaces.templating import render

router = APIRouter()
_K = 5
# 한 줄에 들어갈 질문 길이. api의 상한(200자) 안이다
_QUERY_LIMIT = 200


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(
    request: Request,
    services: ServicesDep,
    q: Annotated[str, Query(max_length=_QUERY_LIMIT)] = "",
    strategy: str = ChunkStrategy.PARAGRAPH.value,
) -> HTMLResponse:
    """GET 폼 하나 — 주소에 질문이 남아 결과를 공유하고 되돌아올 수 있다."""
    chosen = ChunkStrategy(strategy) if strategy in ChunkStrategy else ChunkStrategy.PARAGRAPH
    query = " ".join(q.split())
    hits = await services.documents.search(query, chosen, _K) if query else ()
    context = {
        "section": "documents",
        "query": query,
        "strategy": chosen,
        "strategies": list(ChunkStrategy),
        "hits": hits,
    }
    return render(request, "documents.html", context)
