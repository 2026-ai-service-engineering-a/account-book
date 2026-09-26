from __future__ import annotations

import inspect

from ui.application.ports import ChatAgent
from ui.infrastructure.memory import (
    MemoryBudgetGateway,
    MemoryCatalogGateway,
    MemoryReportGateway,
    MemoryTransactionGateway,
)
from ui.infrastructure.scripted import ScriptedCategorySuggester, ScriptedChatAgent


def test_stand_in_fills_the_port(store, clock):
    # 대입이 곧 계약 검사다. run·decide는 SSE처럼 이벤트를 흘려보내는 async generator다
    port: ChatAgent = ScriptedChatAgent(
        MemoryTransactionGateway(store),
        MemoryReportGateway(store, clock),
        MemoryBudgetGateway(store, clock),
        MemoryCatalogGateway(store),
        ScriptedCategorySuggester(),
        clock,
    )
    assert inspect.isasyncgenfunction(port.run)
    assert inspect.isasyncgenfunction(port.decide)
