from __future__ import annotations

import dataclasses
from datetime import datetime

import pytest

from tests.ui.conftest import FixedClock
from ui.main import create_app


def test_zone_comes_from_clock():
    services = create_app(clock=FixedClock(), seeded=False).state.services
    assert str(services.zone()) == "Asia/Seoul"


def test_naive_clock_is_an_assembly_error():
    services = create_app(clock=FixedClock(), seeded=False).state.services
    broken = dataclasses.replace(services, clock=FixedClock(datetime(2026, 9, 17)))
    with pytest.raises(RuntimeError):
        broken.zone()
