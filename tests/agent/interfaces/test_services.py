from __future__ import annotations

import pytest
from fastapi import FastAPI
from starlette.requests import Request

from agent.interfaces.services import get_services


def test_refuses_an_unassembled_app():
    app = FastAPI()
    app.state.services = None
    request = Request({"type": "http", "app": app})
    with pytest.raises(RuntimeError):
        get_services(request)
