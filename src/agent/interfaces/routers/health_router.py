from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """떠 있는지만 본다. 제공자를 부르지 않는다 — 확인마다 돈이 나가면 안 된다."""
    return {"status": "ok"}
