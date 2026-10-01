from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from api.application.ports import DatabaseProbe


@dataclass(frozen=True, slots=True)
class Services:
    """라우터가 쓰는 포트 묶음. 무엇이 채우는지는 main.py만 안다."""

    database: DatabaseProbe


def get_services(request: Request) -> Services:
    services = request.app.state.services
    if not isinstance(services, Services):
        raise RuntimeError("app.state.services가 조립되지 않았다")
    return services


ServicesDep = Annotated[Services, Depends(get_services)]
