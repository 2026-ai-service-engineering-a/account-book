from __future__ import annotations

import dataclasses
import logging
from datetime import datetime

from agent.application.dto import CaptureExtraction, ExtractionKind
from agent.application.errors import LedgerUnavailable, MalformedOutput, ModelUnavailable
from agent.application.parsers import parse_capture_extraction
from agent.application.ports import LanguageModel
from agent.application.prompts import capture_prompt
from agent.domain.values import CaptureReading, CategoryChoice, Direction, Money

from .classify_category import ClassifyCategory

# 스키마를 못 맞추면 한 번만 다시 시킨다(docs/ai/README.md 2장 원칙 3)
_ATTEMPTS = 2

QUESTION = "질문은 채팅에서 물어 주세요. 여기는 기록을 채우는 칸이에요."
CANCELLED = "승인 취소 문자는 아직 읽지 않아요. 원래 거래를 찾아 직접 고쳐 주세요."
NO_AMOUNT = (
    "금액을 찾지 못했어요. 카드 문자를 붙여넣거나 '오늘 오후 3시 카페 5천원'처럼 적어 주세요."
)
UNREADABLE = "이 한 줄은 읽지 못했어요. 칸을 직접 채워 주세요."
NO_CATEGORY = "지금은 카테고리를 추천할 수 없어요. 직접 골라 주세요."

_log = logging.getLogger(__name__)


class ReadCapture:
    """기록(capture) — 카드 문자나 말로 쓴 한 줄을 거래 칸으로 읽는다.

    값을 뽑고(LLM 1회), 가맹점을 읽었으면 이어서 카테고리를 고른다(RAG, LLM 0~1회). 순서는
    코드가 정한다 — 루프가 아니라 단발 둘을 이은 것이다(docs/ai/agent-loop.md 3장).
    채우기까지만 한다. 저장은 사람이 폼에서 누른다(ui_docs/pages/transaction-form.md 4.4).
    값을 뽑는 LLM에 닿지 못하면 `ModelUnavailable`이 그대로 올라간다 — 번역은 interfaces가 한다.
    """

    def __init__(self, model: LanguageModel, classify: ClassifyCategory | None = None) -> None:
        self._model = model
        self._classify = classify

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
            return await self._with_category(_reading(extraction, text, now))
        return CaptureReading.refused(UNREADABLE)

    async def _with_category(self, reading: CaptureReading) -> CaptureReading:
        """카테고리를 못 골라도 읽은 값은 살린다. 카테고리 칸만 비고 나머지는 채워진다."""
        if self._classify is None or reading.merchant is None:
            return reading
        # 방향을 못 읽었으면 폼의 기본값(지출)으로 고른다.
        # 수입이었다면 사람이 방향을 바꾸고 AI 버튼으로 다시 고른다.
        direction = reading.direction or Direction.EXPENSE
        try:
            choice = await self._classify(reading.merchant, "", direction)
        except (LedgerUnavailable, ModelUnavailable) as error:
            _log.warning("capture classify skipped: %s", type(error).__name__)
            choice = CategoryChoice.abstain(NO_CATEGORY)
        return dataclasses.replace(reading, category=choice)


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
