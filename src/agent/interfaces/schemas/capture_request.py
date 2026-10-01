from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AwareDatetime, BaseModel, Field, field_validator

# 카드 문자 서너 통을 이어 붙여도 이 안이다. 넘으면 한 줄이 아니다.
_TEXT_LIMIT = 2_000


class CaptureRequest(BaseModel):
    """`POST /capture`의 본문. 기준 시각과 타임존은 부르는 쪽이 준다 — agent는 추측하지 않는다
    (development-rules 6.1)."""

    text: str = Field(min_length=1, max_length=_TEXT_LIMIT)
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

    def local_now(self) -> AwareDatetime:
        return self.now.astimezone(ZoneInfo(self.timezone))
