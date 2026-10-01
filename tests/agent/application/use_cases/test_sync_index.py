from __future__ import annotations

import asyncio

import pytest

from agent.application.dto import PendingText
from agent.application.errors import ModelUnavailable
from agent.application.use_cases import SyncIndex
from tests.agent.conftest import FakeEmbedder, FakeLedger


def test_embeds_pending_texts_once_each():
    ledger = FakeLedger(pending=[PendingText("h1", "스타벅스"), PendingText("h2", "김밥천국")])
    embedder = FakeEmbedder()
    assert asyncio.run(SyncIndex(ledger, embedder).run()) == 2
    assert embedder.calls == [["스타벅스", "김밥천국"]]
    assert ledger.puts == {"h1": (4.0, 1.0), "h2": (4.0, 1.0)}


def test_nothing_pending_calls_no_provider():
    embedder = FakeEmbedder()
    assert asyncio.run(SyncIndex(FakeLedger(), embedder).run()) == 0
    assert embedder.calls == []


def test_provider_failure_is_raised_to_the_caller():
    ledger = FakeLedger(pending=[PendingText("h1", "스타벅스")])
    with pytest.raises(ModelUnavailable):
        asyncio.run(SyncIndex(ledger, FakeEmbedder(fail=True)).run())
