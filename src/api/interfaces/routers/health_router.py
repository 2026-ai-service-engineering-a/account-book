from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.interfaces.services import ServicesDep

router = APIRouter(prefix="/v1")


@router.get("/healthz")
def healthz(services: ServicesDep) -> JSONResponse:
    """떠 있고 DB에 닿는가. DB가 없으면 api는 아무 일도 못 하니 503이다.

    동기 함수다 — FastAPI가 스레드풀에서 돌린다(development-rules 6.2).
    """
    if services.database.ping():
        return JSONResponse({"status": "ok"})
    error = {"code": "db_unavailable", "message": "DB에 닿지 못했습니다."}
    return JSONResponse({"error": error}, status_code=503)
