from __future__ import annotations

import json

from mcp_server.domain.values import PeriodName
from mcp_server.infrastructure.contract_file import CONTRACT


def test_same_names_as_the_contract_enum():
    # 바깥 모델이 보는 enum과 우리가 받는 이름이 같아야 한다 — 계약은 agent가 쓴다
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    summarize = next(c for c in contract if c["name"] == "summarize_spending")
    period = summarize["input_schema"]["properties"]["period"]
    assert period["properties"]["name"]["enum"] == [n.value for n in PeriodName]
