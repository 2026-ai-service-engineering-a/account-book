"""문서 화면 — 법령 조각을 찾아 원문을 인용으로 보인다(ui_docs/pages/documents.md)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from ui.application.dto import ChunkStrategy, SearchMode
from ui.interfaces.services import ServicesDep
from ui.interfaces.templating import render

router = APIRouter()
# 한 줄에 들어갈 질문 길이. api의 상한(200자) 안이다
_QUERY_LIMIT = 200


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(
    request: Request,
    services: ServicesDep,
    q: Annotated[str, Query(max_length=_QUERY_LIMIT)] = "",
    strategy: str = ChunkStrategy.PARAGRAPH_ITEM.value,
    mode: str = "",
    action: str = "search",
) -> HTMLResponse:
    """GET 폼 하나 — 주소에 질문이 남아 결과를 공유하고 되돌아올 수 있다.

    기본은 재서 고른 값이다(docs/ai/document-rag.md 6.3) — 항이되 긴 항은 호, agent가 있으면
    하이브리드. 조각 수는 비워 두어 찾는 쪽의 기본(DOC_TOP_K)을 쓴다.
    """
    chosen = ChunkStrategy(strategy) if strategy in ChunkStrategy else ChunkStrategy.PARAGRAPH_ITEM
    by_agent = services.documents_by_agent
    how = SearchMode.HYBRID if by_agent else SearchMode.KEYWORD
    if by_agent and mode in SearchMode:
        how = SearchMode(mode)
    query = " ".join(q.split())
    asking = action == "ask" and bool(query)
    # 묻기는 찾는 방법을 agent의 기본값(DOC_*)에 맡긴다 — 답의 품질이 그 값으로 재어졌다
    answer = await services.answerer.ask(query) if asking else None
    found = (
        await services.documents.search(query, chosen, None, how) if query and not asking else None
    )
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
        "answer": answer,
    }
    return render(request, "documents.html", context)
