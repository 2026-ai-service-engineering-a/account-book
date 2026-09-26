from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse

from ui.interfaces.services import ServicesDep

router = APIRouter()


@router.post("/demo/reset")
async def demo_reset(
    services: ServicesDep,
    filled: Annotated[bool, Form()] = True,
    back: Annotated[str, Form()] = "/",
) -> RedirectResponse:
    """대역 저장소를 비우거나 채운다. 빈 화면 두 종류를 눈으로 보려고 둔다."""
    if services.demo is None:
        raise HTTPException(status_code=404)
    await services.demo.reset(filled)
    # 이 사이트 안의 경로로만 되돌아간다
    target = back if back.startswith("/") and not back.startswith("//") else "/"
    return RedirectResponse(target, status_code=303)
