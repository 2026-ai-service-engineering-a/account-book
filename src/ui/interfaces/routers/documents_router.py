"""문서 화면 — 법령 조각을 찾아 원문을 인용으로 보인다(ui_docs/pages/documents.md)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from ui.application.dto import ChunkStrategy, SearchMode
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
    mode: str = SearchMode.KEYWORD.value,
) -> HTMLResponse:
    """GET 폼 하나 — 주소에 질문이 남아 결과를 공유하고 되돌아올 수 있다.

    찾는 방법의 기본은 낱말이다 — 지금까지의 동작. 무엇을 기본으로 할지는 재서 정한다
    (docs/ai/document-rag.md 7.2).
    """
    chosen = ChunkStrategy(strategy) if strategy in ChunkStrategy else ChunkStrategy.PARAGRAPH
    how = (
        SearchMode(mode)
        if mode in SearchMode and services.documents_by_agent
        else SearchMode.KEYWORD
    )
    query = " ".join(q.split())
    found = await services.documents.search(query, chosen, _K, how) if query else None
    context = {
        "section": "documents",
        "query": query,
        "strategy": chosen,
        "strategies": list(ChunkStrategy),
        "mode": how,
        "modes": list(SearchMode),
        "by_agent": services.documents_by_agent,
        "hits": found.hits if found else (),
        "fell_back": found.fell_back if found else False,
    }
    return render(request, "documents.html", context)
