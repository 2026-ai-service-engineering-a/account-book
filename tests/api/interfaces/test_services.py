from __future__ import annotations

import pytest
from fastapi import FastAPI
from starlette.requests import Request

from api.interfaces.services import get_services


def test_refuses_an_unassembled_app():
    app = FastAPI()
    app.state.services = None
    with pytest.raises(RuntimeError):
        get_services(Request({"type": "http", "app": app}))
