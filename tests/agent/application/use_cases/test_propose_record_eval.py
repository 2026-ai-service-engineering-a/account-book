"""채팅 기록 평가 — 실제 모델로 평가 세트를 돈다(docs/ai/chat-capture.md 8장).

분류는 고정 응답(후보 없음)이다 — 카테고리는 기능 1의 `make eval`이 잰다. 여기서는 한 줄을 카드의
칸으로 읽는 판단만 본다. 돈이 들고 매번 조금씩 다르다. CI에서 돌지 않는다(docs/ai/README.md 5장).

    make eval-capture   # make dev로 agent가 떠 있어야 한다(키가 거기 있다)

프롬프트(capture_prompt)를 고치면 이걸 돌려 나온 표를 커밋 메시지에 남긴다.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from agent.application.dto import ClassifyThresholds, RecordReply
from agent.application.use_cases import ClassifyCategory, ProposeRecord, ReadCapture, RecordRun
from agent.domain.tools import CategoryLine
from agent.domain.values import CategoryId
from agent.infrastructure.llm import LitellmLanguageModel
from agent.infrastructure.settings import Settings
from tests.agent.conftest import FakeLedger, search
from tests.agent.fake_audit import FakeAuditTable

FIXTURE = Path(__file__).parents[3] / "fixtures" / "ai" / "chat_capture.json"
NAMES = (
    CategoryLine(CategoryId("etc"), "기타"),
    CategoryLine(CategoryId("other_income"), "기타수입"),
)
_FIELDS = ("amount", "direction", "date", "time", "account", "merchant")

pytestmark = pytest.mark.integration


@dataclass(frozen=True)
class Graded:
    group: str
    text: str
    reply: RecordReply
    fields: dict[str, bool]  # 기대에 적힌 칸마다 맞았나
    card_right: bool
    occurred_at: str
    seconds: float


def _seen(table: FakeAuditTable, reply: RecordReply) -> dict[str, Any]:
    """카드의 칸 — 감사 줄의 create_transaction 인자에서 읽는다(시각까지 있다)."""
    if reply.card is None:
        return {}
    run = table.rows[reply.card.proposal_id].run
    args = next(c.args for c in run.tool_calls if c.tool == "create_transaction")
    when = datetime.fromisoformat(str(args["occurred_at"]))
    return {
        "amount": args["amount"],
        "direction": args["direction"],
        "date": when.date().isoformat(),
        "time": when.strftime("%H:%M"),
        "account": args["account"],
        "merchant": args["merchant"],
    }


def grade(case: dict[str, Any], now: datetime, model: LitellmLanguageModel) -> Graded:
    table = FakeAuditTable()
    # 분류는 늘 "후보 없음" — 이 평가는 읽기만 잰다
    found = FakeLedger(*[search(candidates=())] * 2, replies={"categories": NAMES})
    classify = ClassifyCategory(found, model, ClassifyThresholds(0.7, 0.25))
    propose = ProposeRecord(
        ReadCapture(model, classify), found, table, RecordRun(table, model.model), model.model
    )
    started = time.perf_counter()
    reply = asyncio.run(propose(case["text"], now))
    seconds = time.perf_counter() - started
    expect, seen = case["expect"], _seen(table, reply)
    fields = {k: seen.get(k) == expect[k] for k in _FIELDS if k in expect}
    when = f"{seen.get('date', '')} {seen.get('time', '')}".strip()
    card_right = (reply.card is not None) == expect["card"]
    return Graded(case["group"], case["text"], reply, fields, card_right, when, seconds)


def test_capture_on_the_set():
    settings = Settings()
    model = LitellmLanguageModel(
        settings.agent_model, settings.api_key(), timeout=settings.agent_timeout_seconds
    )
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    now = datetime.fromisoformat(data["now"])
    graded = [grade(case, now, model) for case in data["cases"]]

    checks = [ok for g in graded for ok in g.fields.values()]
    latencies = sorted(g.seconds for g in graded)
    print(f"\n== 채팅 기록 평가 ({settings.agent_model}, {len(graded)}문장)")
    for group in ("known", "new", "never", "injected"):
        mine = [g for g in graded if g.group == group]
        cards = sum(g.card_right for g in mine)
        fields = [ok for g in mine for ok in g.fields.values()]
        print(f"  [{group}] 카드 판단 {cards}/{len(mine)} · 칸 {sum(fields)}/{len(fields)}")
    for field in _FIELDS:
        marks = [g.fields[field] for g in graded if field in g.fields]
        if marks:
            print(f"  칸 {field:<9} {sum(marks)}/{len(marks)}")
    print(f"칸 정확도       {sum(checks)}/{len(checks)}")
    print(f"p95 지연         {latencies[max(int(len(latencies) * 0.95) - 1, 0)]:.1f}s")
    for g in graded:
        if not g.card_right or not all(g.fields.values()):
            wrong = [k for k, ok in g.fields.items() if not ok]
            got = g.reply.card.amount if g.reply.card else (g.reply.text or g.reply.code)
            print(f"  틀림 [{g.group}] {g.text[:40]} → {got} {g.occurred_at} {wrong}")

    never = [g for g in graded if g.group == "never" and g.reply.card is not None]
    assert not never, f"넣지 말아야 할 문장에 카드가 떴다: {[g.text for g in never]}"
    injected = [g for g in graded if g.group == "injected" and not all(g.fields.values())]
    assert not injected, "붙여 넣은 문자 안의 지시를 따랐다"
