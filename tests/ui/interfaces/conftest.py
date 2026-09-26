from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from tests.ui.conftest import FixedClock
from ui.main import create_app


@pytest.fixture
def empty_client() -> TestClient:
    return TestClient(create_app(clock=FixedClock(), seeded=False, token_delay=0))


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(clock=FixedClock(), seeded=True, token_delay=0))


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
