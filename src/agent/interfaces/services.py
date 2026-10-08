from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from agent.application.use_cases import AnswerQuestion, ClassifyCategory, ReadCapture


@dataclass(frozen=True, slots=True)
class Services:
    """라우터가 쓰는 유스케이스 묶음. 무엇으로 조립했는지는 main.py만 안다."""

    read_capture: ReadCapture
    classify: ClassifyCategory
    answer: AnswerQuestion


def get_services(request: Request) -> Services:
    services = request.app.state.services
    if not isinstance(services, Services):
        raise RuntimeError("app.state.services가 조립되지 않았다")
    return services


ServicesDep = Annotated[Services, Depends(get_services)]
