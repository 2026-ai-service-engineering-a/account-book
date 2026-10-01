from __future__ import annotations

import re
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from tests.ui.conftest import FixedClock
from ui.application.dto import CategorySuggestion, Direction, MessageReading
from ui.main import create_app


@pytest.fixture
def empty_client() -> TestClient:
    return TestClient(create_app(clock=FixedClock(), seeded=False, token_delay=0, capture_delay=0))


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(clock=FixedClock(), seeded=True, token_delay=0, capture_delay=0))


def sse_events(text: str) -> list[tuple[str, str]]:
    events = []
    for block in filter(None, text.split("\n\n")):
        lines = block.split("\n")
        name = lines[0].removeprefix("event: ")
        data = "\n".join(line.removeprefix("data: ") for line in lines[1:])
        events.append((name, data))
    return events


def extract(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    assert match is not None, pattern
    return match.group(1)


class FixedSuggester:
    """늘 같은 제안을 내는 카테고리 고르기. 몇 번 불렸는지 센다."""

    def __init__(self, suggestion: CategorySuggestion) -> None:
        self._suggestion = suggestion
        self.calls = 0

    async def suggest(self, merchant: str, memo: str, direction: Direction) -> CategorySuggestion:
        self.calls += 1
        return self._suggestion


class FixedReader:
    """늘 같은 결과를 내는 한 줄 읽기."""

    def __init__(self, reading: MessageReading) -> None:
        self._reading = reading

    async def read(self, text: str, now: datetime) -> MessageReading:
        return self._reading
