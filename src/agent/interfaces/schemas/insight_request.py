from __future__ import annotations

from typing import Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AwareDatetime, BaseModel, Field, field_validator, model_validator


class InsightRequest(BaseModel):
    """`POST /insights`의 본문 — 리포트의 달(YYYY-MM)과 기준 시각·타임존.

    아직 오지 않은 달은 받지 않는다. 기준 시각은 부르는 쪽이 준다(development-rules 6.1).
    """

    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    now: AwareDatetime
    timezone: str

    @field_validator("timezone")
    @classmethod
    def _known_zone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(f"모르는 타임존이다: {value}") from error
        return value

    @model_validator(mode="after")
    def _not_ahead(self) -> Self:
        if self.month > f"{self.local_now():%Y-%m}":
            raise ValueError("아직 오지 않은 달이다")
        return self

    def local_now(self) -> AwareDatetime:
        return self.now.astimezone(ZoneInfo(self.timezone))
