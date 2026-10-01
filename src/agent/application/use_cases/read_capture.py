from __future__ import annotations

from datetime import datetime

from agent.application.dto import CaptureExtraction, ExtractionKind
from agent.application.errors import MalformedOutput
from agent.application.parsers import parse_capture_extraction
from agent.application.ports import LanguageModel
from agent.application.prompts import capture_prompt
from agent.domain.values import CaptureReading, Money

# 스키마를 못 맞추면 한 번만 다시 시킨다(docs/ai/README.md 2장 원칙 3)
_ATTEMPTS = 2

QUESTION = "질문은 채팅에서 물어 주세요. 여기는 기록을 채우는 칸이에요."
CANCELLED = "승인 취소 문자는 아직 읽지 않아요. 원래 거래를 찾아 직접 고쳐 주세요."
NO_AMOUNT = (
    "금액을 찾지 못했어요. 카드 문자를 붙여넣거나 '오늘 오후 3시 카페 5천원'처럼 적어 주세요."
)
UNREADABLE = "이 한 줄은 읽지 못했어요. 칸을 직접 채워 주세요."


class ReadCapture:
    """기록(capture) — 카드 문자나 말로 쓴 한 줄을 거래 칸으로 읽는다. 단발, LLM 1회.

    채우기까지만 한다. 저장은 사람이 폼에서 누른다(ui_docs/pages/transaction-form.md 4.4).
    제공자에 닿지 못하면 `ModelUnavailable`이 그대로 올라간다 — 번역은 interfaces가 한다.
    """

    def __init__(self, model: LanguageModel) -> None:
        self._model = model

    async def __call__(self, text: str, now: datetime) -> CaptureReading:
        """`now`는 사용자 타임존의 기준 시각. "어제"와 "09/16"의 연도를 여기서 정한다."""
        if now.tzinfo is None:
            raise ValueError("기준 시각은 aware여야 한다")
        prompt = capture_prompt(text)
        for _ in range(_ATTEMPTS):
            try:
                extraction = parse_capture_extraction(await self._model.complete_json(prompt))
            except MalformedOutput:
                continue
            return _reading(extraction, text, now)
        return CaptureReading.refused(UNREADABLE)


def _reading(extraction: CaptureExtraction, text: str, now: datetime) -> CaptureReading:
    if extraction.kind is ExtractionKind.QUESTION:
        return CaptureReading.refused(QUESTION)
    if extraction.kind is ExtractionKind.CANCELLATION:
        return CaptureReading.refused(CANCELLED)
    if extraction.kind is ExtractionKind.UNREADABLE or extraction.amount == 0:
        return CaptureReading.refused(NO_AMOUNT)
    try:
        amount = Money(extraction.amount)
    except ValueError:
        return CaptureReading.refused(NO_AMOUNT)
    return CaptureReading(
        direction=extraction.direction,
        amount=amount,
        occurred_at=extraction.when.resolve(now),
        payment_method=extraction.payment_method,
        merchant=_grounded(extraction.merchant, text),
    )


def _grounded(merchant: str, text: str) -> str | None:
    """가맹점명은 보낸 글 안에 있어야 한다. 없으면 모델이 지어낸 것이라 버린다.

    띄어쓰기만 다른 것("김밥 천국")은 같은 이름으로 본다.
    """
    if not merchant:
        return None
    squeeze = str.maketrans("", "", " \t\n")
    return merchant if merchant.translate(squeeze) in text.translate(squeeze) else None
