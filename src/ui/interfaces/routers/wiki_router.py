from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ui.interfaces.ai_map import SEATS
from ui.interfaces.services import ServicesDep
from ui.interfaces.templating import render

router = APIRouter()


@router.get("/wiki", response_class=HTMLResponse)
async def wiki_page(request: Request, services: ServicesDep) -> HTMLResponse:
    """AI 위키 한 장. 아무 서비스도 부르지 않는다(ui_docs/pages/wiki.md 2장)."""
    context = {
        "section": "wiki",
        "seats": SEATS,
        # 대역 모드면 모든 AI 자리에 각본 대역이 서 있다
        "stand_in_mode": services.demo is not None,
        "capture_on": services.capture is not None,
    }
    return render(request, "wiki.html", context)
